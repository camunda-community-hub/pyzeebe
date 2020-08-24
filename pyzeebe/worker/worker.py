import asyncio
import logging
import socket
from typing import List, Callable, Generator, Tuple, Awaitable

from pyzeebe.common.exceptions import TaskNotFoundException
from pyzeebe.decorators.zeebe_decorator_base import ZeebeDecoratorBase
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.task.task import Task
from pyzeebe.task.task_context import TaskContext
from pyzeebe.task.task_decorator import TaskDecorator
from pyzeebe.task.task_status_controller import TaskStatusController


class ZeebeWorker(ZeebeDecoratorBase):
    """A zeebe worker that can connect to a zeebe instance and perform tasks."""

    def __init__(self, name: str = None, request_timeout: int = 1000, hostname: str = None, port: int = None,
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
        self.loop = asyncio.get_event_loop()

    def work(self):
        for task in self.tasks:
            asyncio.ensure_future(self._handle_task(task))
        self.loop.run_forever()

    async def _handle_task(self, task: Task):
        logging.debug(f'Handling task {task}')
        while self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection:
            if self.zeebe_adapter.retrying_connection:
                logging.debug(f'Retrying connection to {self.zeebe_adapter._connection_uri}')
                # time.sleep(5)
                continue

            for task_context in self._get_task_contexts(task):
                logging.debug(f'Creating task: {task_context.key}')
                self.loop.create_task(task.handler(task_context))

    def _get_task_contexts(self, task: Task) -> Generator[TaskContext, None, None]:
        logging.debug(f'Activating jobs for task: {task}')
        return self.zeebe_adapter.activate_jobs(task_type=task.type, worker=self.name, timeout=task.timeout,
                                                max_jobs_to_activate=task.max_jobs_to_activate,
                                                variables_to_fetch=task.variables_to_fetch,
                                                request_timeout=self.request_timeout)

    def add_task(self, task: Task) -> None:
        task.handler = self._create_zeebe_task_handler(task)
        self.tasks.append(task)

    def _create_zeebe_task_handler(self, task: Task) -> Callable[[TaskContext], Awaitable[TaskContext]]:
        before_decorator_runner = self._create_before_decorator_runner(task)
        after_decorator_runner = self._create_after_decorator_runner(task)

        async def task_handler(context: TaskContext):
            try:
                context = before_decorator_runner(context)
                context.variables = task.inner_function(**context.variables)
                context = after_decorator_runner(context)
                logging.debug(f'Completing job: {context}')
                self.zeebe_adapter.complete_job(job_key=context.key, variables=context.variables)
                return context
            except Exception as e:
                logging.debug(f'Failed job: {str(e)}. Calling task exception_handler with context: {context}.')
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
