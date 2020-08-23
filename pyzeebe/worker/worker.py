import socket
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Generator, Dict, Tuple

from pyzeebe.common.exceptions import TaskNotFoundException, NotEnoughTasksException
from pyzeebe.decorators.zeebe_decorator_base import ZeebeDecoratorBase
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.task.task import Task
from pyzeebe.task.task_context import TaskContext
from pyzeebe.task.task_decorator import TaskDecorator
from pyzeebe.task.task_status_controller import TaskStatusController


# TODO: Add support for async tasks
class ZeebeWorker(ZeebeDecoratorBase):
    """A zeebe worker that can connect to a zeebe instance and perform tasks."""

    def __init__(self, name: str = None, request_timeout: int = 0, hostname: str = None, port: int = None,
                 before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
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
        self.zeebe_adapter = ZeebeAdapter(hostname=hostname, port=port)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.tasks = []

    def work(self):
        if len(self.tasks) > 0:
            executor = ThreadPoolExecutor(max_workers=len(self.tasks))
            executor.map(self._handle_task, self.tasks)
            executor.shutdown(wait=True)
        else:
            raise NotEnoughTasksException('Worker needs tasks in order to work')

    def _handle_task(self, task: Task):
        while self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection:
            if self.zeebe_adapter.retrying_connection:
                continue

            self._handle_task_contexts(task)

    def _handle_task_contexts(self, task: Task):
        executor = ThreadPoolExecutor()
        executor.map(task.handler, self._get_task_contexts(task))
        executor.shutdown(wait=False)  # Do not wait for tasks to finish

    def _get_task_contexts(self, task: Task) -> Generator[TaskContext, None, None]:
        return self.zeebe_adapter.activate_jobs(task_type=task.type, worker=self.name, timeout=task.timeout,
                                                max_jobs_to_activate=task.max_jobs_to_activate,
                                                variables_to_fetch=task.variables_to_fetch,
                                                request_timeout=self.request_timeout)

    def add_task(self, task: Task) -> None:
        task.handler = self._create_zeebe_task_handler(task)
        self.tasks.append(task)

    def _create_zeebe_task_handler(self, task: Task) -> Callable[[TaskContext], Dict]:
        before_decorator_runner = self._create_before_decorator_runner(task)
        after_decorator_runner = self._create_after_decorator_runner(task)

        def task_handler(context: TaskContext):
            try:
                context = before_decorator_runner(context)
                context.variables = task.inner_function(**context.variables)
                context = after_decorator_runner(context)
                self.zeebe_adapter.complete_job(job_key=context.key, variables=context.variables)
                return context.variables
            except Exception as e:
                task.exception_handler(e, context, TaskStatusController(context, self.zeebe_adapter))
                return e

        return task_handler

    def _create_before_decorator_runner(self, task: Task) -> Callable[[TaskContext], TaskContext]:
        decorators = task._before.copy()
        decorators.extend(self._before)
        return self._create_decorator_runner(decorators)

    def _create_after_decorator_runner(self, task: Task) -> Callable[[TaskContext], TaskContext]:
        decorators = self._after.copy()
        decorators.extend(task._after)
        return self._create_decorator_runner(decorators)

    @staticmethod
    def _create_decorator_runner(decorators: List[TaskDecorator]) -> Callable[[TaskContext], TaskContext]:
        def decorator_runner(context: TaskContext):
            for decorator in decorators:
                context = decorator(context)
            return context

        return decorator_runner

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
        raise TaskNotFoundException(f"Could not find task {task_type}")
