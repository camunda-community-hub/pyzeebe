import socket
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Generator, Dict, Tuple

from pyz.decorators.base_zeebe_decorator import BaseZeebeDecorator
from pyz.decorators.task_decorator import TaskDecorator
from pyz.exceptions import TaskNotFoundException
from pyz.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyz.task.job_context import JobContext
from pyz.task.task import Task
from pyz.task.task_status_setter import TaskStatusSetter


# TODO: Add support for async tasks
class ZeebeWorker(BaseZeebeDecorator):
    def __init__(self, name: str = None, request_timeout: int = 0, hostname: str = None, port: int = None,
                 before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        super().__init__(before, after)
        self.zeebe_adapter = ZeebeAdapter(hostname=hostname, port=port)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.tasks = []

    def work(self):
        executor = ThreadPoolExecutor(max_workers=len(self.tasks))
        executor.map(self.handle_task, self.tasks)
        executor.shutdown(wait=True)

    def handle_task(self, task: Task):
        while self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection:
            if self.zeebe_adapter.retrying_connection:
                continue

            self.handle_task_jobs(task)

    def handle_task_jobs(self, task: Task):
        executor = ThreadPoolExecutor()
        executor.map(task.handler, self._get_jobs(task))
        executor.shutdown(wait=False)  # Do not wait for tasks to finish

    def _get_jobs(self, task: Task) -> Generator[JobContext, None, None]:
        return self.zeebe_adapter.activate_jobs(task_type=task.type, worker=self.name, timeout=task.timeout,
                                                max_jobs_to_activate=task.max_jobs_to_activate,
                                                variables_to_fetch=task.variables_to_fetch,
                                                request_timeout=self.request_timeout)

    def add_task(self, task: Task) -> None:
        task.handler = self.create_zeebe_task_handler(task)
        self.tasks.append(task)

    def create_zeebe_task_handler(self, task: Task) -> Callable[[JobContext], Dict]:
        before_decorator_runner = self._create_before_decorator_runner(task)
        after_decorator_runner = self._create_after_decorator_runner(task)

        def task_handler(context: JobContext):
            try:
                context = before_decorator_runner(context)
                context.variables = task.inner_function(**context.variables)
                context = after_decorator_runner(context)
                self.zeebe_adapter.complete_job(job_key=context.key, variables=context.variables)
                return context.variables
            except Exception as e:
                task.exception_handler(e, context, TaskStatusSetter(context, self.zeebe_adapter))
                return e

        return task_handler

    def _create_before_decorator_runner(self, task: Task) -> Callable[[JobContext], JobContext]:
        decorators = task._before.copy()
        decorators.extend(self._before)
        return self._create_decorator_runner(decorators)

    def _create_after_decorator_runner(self, task: Task) -> Callable[[JobContext], JobContext]:
        decorators = self._after.copy()
        decorators.extend(task._after)
        return self._create_decorator_runner(decorators)

    @staticmethod
    def _create_decorator_runner(decorators: List[TaskDecorator]) -> Callable[[JobContext], JobContext]:
        def decorator_runner(context: JobContext):
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
