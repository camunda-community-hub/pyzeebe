import logging
import socket
from threading import Thread, Event
from typing import List, Callable, Generator, Tuple

from pyzeebe.common.exceptions import TaskNotFound
from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.decorators.zeebe_decorator_base import ZeebeDecoratorBase
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.job.job_status_controller import JobStatusController
from pyzeebe.task.task import Task
from pyzeebe.task.task_decorator import TaskDecorator


class ZeebeWorker(ZeebeDecoratorBase):
    """A zeebe worker that can connect to a zeebe instance and perform tasks."""

    def __init__(self, name: str = None, request_timeout: int = 0, hostname: str = None, port: int = None,
                 credentials: BaseCredentials = None, secure_connection: bool = False,
                 before: List[TaskDecorator] = None,
                 after: List[TaskDecorator] = None):
        """
        Args:
            hostname (str): Zeebe instance hostname
            port (int): Port of the zeebe
            name (str): Name of zeebe worker
            request_timeout (int): Longpolling timeout for getting tasks from zeebe. If 0 default value is used
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
        """
        super().__init__(before, after)
        self.zeebe_adapter = ZeebeAdapter(hostname=hostname, port=port, credentials=credentials,
                                          secure_connection=secure_connection)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.tasks: List[Task] = []
        self.stop_event = Event()

    def work(self) -> None:
        """
        Start the worker. The worker will poll zeebe for jobs of each task in a different thread.
        """
        for task in self.tasks:
            task_thread = Thread(target=self._handle_task, args=(task,))
            task_thread.start()

    def stop(self):
        """
        Stop the worker. This will wait for all tasks to complete before stopping
        """
        self.stop_event.set()

    def _handle_task(self, task: Task) -> None:
        logging.debug(f"Handling task {task}")
        while not self.stop_event.is_set() and self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection:
            if self.zeebe_adapter.retrying_connection:
                logging.warning(f"Retrying connection to {self.zeebe_adapter.connection_uri or 'zeebe'}")
                continue

            self._handle_jobs(task)

    def _handle_jobs(self, task: Task) -> None:
        for task_context in self._get_jobs(task):
            thread = Thread(target=task.handler, args=(task_context,))
            logging.debug(f"Running job: {task_context}")
            thread.start()

    def _get_jobs(self, task: Task) -> Generator[Job, None, None]:
        logging.debug(f"Activating jobs for task: {task}")
        return self.zeebe_adapter.activate_jobs(task_type=task.type, worker=self.name, timeout=task.timeout,
                                                max_jobs_to_activate=task.max_jobs_to_activate,
                                                variables_to_fetch=task.variables_to_fetch,
                                                request_timeout=self.request_timeout)

    def add_task(self, task: Task) -> None:
        task.handler = self._create_task_handler(task)
        self.tasks.append(task)

    def _create_task_handler(self, task: Task) -> Callable[[Job], Job]:
        before_decorator_runner = self._create_before_decorator_runner(task)
        after_decorator_runner = self._create_after_decorator_runner(task)

        def task_handler(job: Job) -> Job:
            job = before_decorator_runner(job)
            job, task_succeeded = self._run_task_inner_function(task, job)
            job = after_decorator_runner(job)
            if task_succeeded:
                self._complete_job(job)
            return job

        return task_handler

    def _run_task_inner_function(self, task: Task, job: Job) -> Tuple[Job, bool]:
        task_succeeded = False
        try:
            job.variables = task.inner_function(**job.variables)
            task_succeeded = True
        except Exception as e:
            logging.debug(f"Failed job: {job}. Error: {e}.")
            task.exception_handler(e, job, JobStatusController(job, self.zeebe_adapter))
        finally:
            return job, task_succeeded

    def _complete_job(self, job: Job) -> None:
        try:
            logging.debug(f"Completing job: {job}")
            self.zeebe_adapter.complete_job(job_key=job.key, variables=job.variables)
        except Exception as e:
            logging.warning(f"Failed to complete job: {job}. Error: {e}")

    def _create_before_decorator_runner(self, task: Task) -> Callable[[Job], Job]:
        decorators = task._before.copy()
        decorators.extend(self._before)
        return self._create_decorator_runner(decorators)

    def _create_after_decorator_runner(self, task: Task) -> Callable[[Job], Job]:
        decorators = self._after.copy()
        decorators.extend(task._after)
        return self._create_decorator_runner(decorators)

    @staticmethod
    def _create_decorator_runner(decorators: List[TaskDecorator]) -> Callable[[Job], Job]:
        def decorator_runner(job: Job):
            for decorator in decorators:
                job = ZeebeWorker._run_decorator(decorator, job)
            return job

        return decorator_runner

    @staticmethod
    def _run_decorator(decorator: TaskDecorator, job: Job) -> Job:
        try:
            return decorator(job)
        except Exception as e:
            logging.warning(f"Failed to run decorator {decorator}. Error: {e}")
            return job

    def remove_task(self, task_type: str) -> Task:
        task_index = self._get_task_index(task_type)
        return self.tasks.pop(task_index)

    def get_task(self, task_type: str) -> Task:
        return self._get_task_and_index(task_type)[0]

    def _get_task_index(self, task_type: str) -> int:
        return self._get_task_and_index(task_type)[-1]

    def _get_task_and_index(self, task_type: str) -> Tuple[Task, int]:
        for index, task in enumerate(self.tasks):
            if task.type == task_type:
                return task, index
        raise TaskNotFound(f"Could not find task {task_type}")
