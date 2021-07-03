import asyncio
import logging
import socket
from typing import List

from pyzeebe import TaskDecorator
from pyzeebe.connection.connection_utils import merge_options
from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.worker.job_executor import JobExecutor
from pyzeebe.worker.job_poller import JobPoller
from pyzeebe.worker.task_router import ZeebeTaskRouter
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)


class ZeebeWorker(ZeebeTaskRouter):
    """A zeebe worker that can connect to a zeebe instance and perform tasks."""

    def __init__(self, name: str = None, request_timeout: int = 0, hostname: str = None, port: int = None,
                 credentials: BaseCredentials = None, secure_connection: bool = False,
                 before: List[TaskDecorator] = None, after: List[TaskDecorator] = None,
                 max_connection_retries: int = 10, watcher_max_errors_factor: int = 3,
                 max_task_count: int = 32):
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
            max_task_count (int): The maximum amount of tasks the worker can handle simultaniously
        """
        super().__init__(before, after)
        options = merge_options(hostname, port, credentials, secure_connection)
        self.zeebe_adapter = ZeebeAdapter(hostname=options.hostname, port=options.port, credentials=options.credentials,
                                          secure_connection=options.secure_connection,
                                          max_connection_retries=max_connection_retries)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.watcher_max_errors_factor = watcher_max_errors_factor
        self._watcher_thread = None
        self.max_task_count = max_task_count
        self._task_state = TaskState()
        self._job_pollers: List[JobPoller] = []
        self._job_executors: List[JobExecutor] = []

    async def work(self) -> None:
        """
        Start the worker. The worker will poll zeebe for jobs of each task in a different thread.

        Raises:
            ActivateJobsRequestInvalidError: If one of the worker's task has invalid types
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        self.zeebe_adapter.connect()
        self._job_executors, self._job_pollers = [], []

        for task in self.tasks:
            jobs_queue: asyncio.Queue = asyncio.Queue()
            poller = JobPoller(self.zeebe_adapter, task, jobs_queue,
                               self.name, self.request_timeout, self._task_state, self.max_task_count)
            executor = JobExecutor(task, jobs_queue, self._task_state)
            self._job_pollers.append(poller)
            self._job_executors.append(executor)

        coroutines = [poller.poll() for poller in self._job_pollers] + \
            [executor.execute() for executor in self._job_executors]

        return await asyncio.gather(*coroutines)

    async def stop(self) -> None:
        """
        Stop the worker. This will emit a signal asking tasks to complete the current task and stop polling for new.
        """
        for poller in self._job_pollers:
            await poller.stop()

        for executor in self._job_executors:
            await executor.stop()

        await self.zeebe_adapter.disconnect()

    def include_router(self, *routers: ZeebeTaskRouter) -> None:
        """
        Adds all router's tasks to the worker.

        Raises:
            DuplicateTaskTypeError: If a task from the router already exists in the worker

        """
        for router in routers:
            for task in router.tasks:
                task.config = self._add_decorators_to_config(task.config)
                self._add_task(task)
