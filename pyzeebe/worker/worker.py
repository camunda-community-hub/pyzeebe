import logging
import socket
import time
from threading import Thread, Event
from typing import List, Callable, Generator, Tuple, Dict, Union

from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.exceptions.pyzeebe_exceptions import MaxConsecutiveTaskThreadError
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.task import Task
from pyzeebe.task.task_decorator import TaskDecorator
from pyzeebe.worker.task_handler import ZeebeTaskHandler, default_exception_handler
from pyzeebe.worker.task_router import ZeebeTaskRouter

logger = logging.getLogger(__name__)


class ZeebeWorker(ZeebeTaskHandler):
    """A zeebe worker that can connect to a zeebe instance and perform tasks."""

    def __init__(self, name: str = None, request_timeout: int = 0, hostname: str = None, port: int = None,
                 credentials: BaseCredentials = None, secure_connection: bool = False,
                 before: List[TaskDecorator] = None, after: List[TaskDecorator] = None,
                 max_connection_retries: int = 10, watcher_max_errors_factor: int = 3):
        """
        Args:
            hostname (str): Zeebe instance hostname
            port (int): Port of the zeebe
            name (str): Name of zeebe worker
            request_timeout (int): Longpolling timeout for getting tasks from zeebe. If 0 default value is used
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
            max_connection_retries (int): Amount of connection retries before worker gives up on connecting to zeebe. To setup with infinite retries use -1
            watcher_max_errors_factor (int): Number of consequtive errors for a task watcher will accept before raising MaxConsecutiveTaskThreadError
        """
        super().__init__(before, after)
        self.zeebe_adapter = ZeebeAdapter(hostname=hostname, port=port, credentials=credentials,
                                          secure_connection=secure_connection,
                                          max_connection_retries=max_connection_retries)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.stop_event = Event()
        self._task_threads: Dict[str, Thread] = {}
        self.watcher_max_errors_factor = watcher_max_errors_factor
        self._watcher_thread  = None

    def work(self, watch: bool = False) -> None:
        """
        Start the worker. The worker will poll zeebe for jobs of each task in a different thread.

        Args:
            watch (bool): Start a watcher thread that restarts task threads on error

        Raises:
            ActivateJobsRequestInvalid: If one of the worker's task has invalid types
            ZeebeBackPressure: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailable: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        for task in self.tasks:
            task_thread = self._start_task_thread(task)
            self._task_threads[task.type] = task_thread

        if watch:
            self._start_watcher_thread()

    def _start_task_thread(self, task: Task) -> Thread:
        if self.stop_event.is_set():
            raise RuntimeError("Tried to start a task with stop_event set")
        logger.debug(f"Starting task thread for {task.type}")
        task_thread = Thread(target=self._handle_task,
                             args=(task,),
                             name=f"{self.__class__.__name__}-Task-{task.type}")
        task_thread.start()
        return task_thread

    def _start_watcher_thread(self):
        self._watcher_thread = Thread(target=self._watch_task_threads,
                                      name=f"{self.__class__.__name__}-Watch")
        self._watcher_thread.start()

    def stop(self, wait: bool = False) -> None:
        """
        Stop the worker. This will emit a signal asking tasks to complete the current task and stop polling for new.

        Args:
            wait (bool): Wait for all tasks to complete
        """
        self.stop_event.set()
        if wait:
            self._join_task_threads()

    def _join_task_threads(self) -> None:
        logger.debug("Waiting for threads to join")
        while self._task_threads:
            _, thread = self._task_threads.popitem()
            thread.join()
        logger.debug("All threads joined")

    def _watch_task_threads(self, frequency: int = 10) -> None:
        logger.debug("Starting task thread watch")
        try:
            self._watch_task_threads_runner(frequency)
        except Exception as err:
            if isinstance(err, MaxConsecutiveTaskThreadError):
                logger.debug("Stopping worker due to too many errors.")
            else:
                logger.debug("An unhandled exception occured when watching threads, stopping worker")
            self.stop()
            raise
        logger.info(f"Watcher stopping (stop_event={self.stop_event.is_set()}, "
                    f"task_threads list lenght={len(self._task_threads)})")

    def _should_handle_task(self) -> bool:
        return not self.stop_event.is_set() and (self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection)

    def _should_watch_threads(self) -> bool:
        return not self.stop_event.is_set() and bool(self._task_threads)

    def _watch_task_threads_runner(self, frequency: int = 10) -> None:
        consecutive_errors = {}
        while self._should_watch_threads():
            logger.debug("Checking task thread status")
            # converting to list to avoid "RuntimeError: dictionary changed size during iteration"
            for task_type in list(self._task_threads.keys()):
                consecutive_errors.setdefault(task_type, 0)
                # thread might be none, if dict changed size, in that case we'll consider it
                # an error, and check if we should handle it
                thread = self._task_threads.get(task_type)
                if not thread or not thread.is_alive():
                    consecutive_errors[task_type] += 1
                    self._check_max_errors(consecutive_errors[task_type], task_type)
                    self._handle_not_alive_thread(task_type)
                else:
                    consecutive_errors[task_type] = 0
            time.sleep(frequency)

    def _handle_not_alive_thread(self, task_type: str):
        if self._should_handle_task():
            logger.warning(f"Task thread {task_type} is not alive, restarting")
            self._restart_task_thread(task_type)
        else:
            logger.warning(f"Task thread {task_type} is not alive, but condition not met for restarting")

    def _check_max_errors(self, consecutive_errors: int, task_type: str):
        if consecutive_errors >= self.watcher_max_errors_factor:
            raise MaxConsecutiveTaskThreadError(f"Number of consecutive errors ({consecutive_errors}) exceeded "
                                                f"max allowed number of errors ({self.watcher_max_errors_factor}) "
                                                f" for task {task_type}", task_type)

    def _restart_task_thread(self, task_type: str) -> None:
        task = self.get_task(task_type)
        self._task_threads[task_type] = self._start_task_thread(task)

    def _handle_task(self, task: Task) -> None:
        logger.debug(f"Handling task {task}")
        retries = 0
        while self._should_handle_task():
            if self.zeebe_adapter.retrying_connection:
                if retries % 10 == 0:
                    logger.debug(f"Waiting for connection to {self.zeebe_adapter.connection_uri or 'zeebe'}")
                retries += 1
                time.sleep(0.5)
                continue

            self._handle_jobs(task)
        logger.info(f"Handle task thread for {task.type} ending")

    def _handle_jobs(self, task: Task) -> None:
        for job in self._get_jobs(task):
            thread = Thread(target=task.handler,
                            args=(job,),
                            name=f"{self.__class__.__name__}-Job-{job.type}")
            logger.debug(f"Running job: {job}")
            thread.start()

    def _get_jobs(self, task: Task) -> Generator[Job, None, None]:
        logger.debug(f"Activating jobs for task: {task}")
        return self.zeebe_adapter.activate_jobs(task_type=task.type, worker=self.name, timeout=task.timeout,
                                                max_jobs_to_activate=task.max_jobs_to_activate,
                                                variables_to_fetch=task.variables_to_fetch,
                                                request_timeout=self.request_timeout)

    def include_router(self, *routers: ZeebeTaskRouter) -> None:
        """
        Adds all router's tasks to the worker.

        Raises:
            DuplicateTaskType: If a task from the router already exists in the worker

        """
        for router in routers:
            for task in router.tasks:
                self._add_task(task)

    def _dict_task(self, task_type: str, exception_handler: ExceptionHandler = default_exception_handler,
                   timeout: int = 10000, max_jobs_to_activate: int = 32, before: List[TaskDecorator] = None,
                   after: List[TaskDecorator] = None, variables_to_fetch: List[str] = None):
        def wrapper(fn: Callable[..., Dict]):
            nonlocal variables_to_fetch
            if not variables_to_fetch:
                variables_to_fetch = self._get_parameters_from_function(fn)

            task = Task(task_type=task_type, task_handler=fn, exception_handler=exception_handler, timeout=timeout,
                        max_jobs_to_activate=max_jobs_to_activate, before=before, after=after,
                        variables_to_fetch=variables_to_fetch)
            self._add_task(task)

            return fn

        return wrapper

    def _non_dict_task(self, task_type: str, variable_name: str,
                       exception_handler: ExceptionHandler = default_exception_handler, timeout: int = 10000,
                       max_jobs_to_activate: int = 32, before: List[TaskDecorator] = None,
                       after: List[TaskDecorator] = None, variables_to_fetch: List[str] = None):
        def wrapper(fn: Callable[..., Union[str, bool, int, List]]):
            nonlocal variables_to_fetch
            if not variables_to_fetch:
                variables_to_fetch = self._get_parameters_from_function(fn)

            dict_fn = self._single_value_function_to_dict(variable_name=variable_name, fn=fn)

            task = Task(task_type=task_type, task_handler=dict_fn, exception_handler=exception_handler, timeout=timeout,
                        max_jobs_to_activate=max_jobs_to_activate, before=before, after=after,
                        variables_to_fetch=variables_to_fetch)
            self._add_task(task)

            return fn

        return wrapper

    def _add_task(self, task: Task) -> None:
        self._is_task_duplicate(task.type)
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

    @staticmethod
    def _run_task_inner_function(task: Task, job: Job) -> Tuple[Job, bool]:
        task_succeeded = False
        try:
            job.variables = task.inner_function(**job.variables)
            task_succeeded = True
        except Exception as e:
            logger.debug(f"Failed job: {job}. Error: {e}.")
            task.exception_handler(e, job)
        finally:
            return job, task_succeeded

    def _complete_job(self, job: Job) -> None:
        try:
            logger.debug(f"Completing job: {job}")
            self.zeebe_adapter.complete_job(job_key=job.key, variables=job.variables)
        except Exception as e:
            logger.warning(f"Failed to complete job: {job}. Error: {e}")

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
            logger.warning(f"Failed to run decorator {decorator}. Error: {e}")
            return job
