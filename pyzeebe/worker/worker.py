import asyncio
import logging
import socket
from typing import List, Optional

import grpc

from pyzeebe import TaskDecorator
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.worker.job_executor import JobExecutor
from pyzeebe.worker.job_poller import JobPoller
from pyzeebe.worker.task_router import ZeebeTaskRouter
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)


class ZeebeWorker(ZeebeTaskRouter):
    """A zeebe worker that can connect to a zeebe instance and perform tasks."""

    def __init__(
        self,
        grpc_channel: grpc.aio.Channel,
        name: Optional[str] = None,
        request_timeout: int = 0,
        before: List[TaskDecorator] = None,
        after: List[TaskDecorator] = None,
        max_connection_retries: int = 10,
        watcher_max_errors_factor: int = 3,
        poll_retry_delay: int = 5,
    ):
        """
        Args:
            grpc_channel (grpc.aio.Channel): GRPC Channel connected to a Zeebe gateway
            name (str): Name of zeebe worker
            request_timeout (int): Longpolling timeout for getting tasks from zeebe. If 0 default value is used
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
            max_connection_retries (int): Amount of connection retries before worker gives up on connecting to zeebe. To setup with infinite retries use -1
            watcher_max_errors_factor (int): Number of consecutive errors for a task watcher will accept before raising MaxConsecutiveTaskThreadError
            poll_retry_delay (int): The number of seconds to wait before attempting to poll again when reaching max amount of running jobs
        """
        super().__init__(before, after)
        self.zeebe_adapter = ZeebeAdapter(grpc_channel, max_connection_retries)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.watcher_max_errors_factor = watcher_max_errors_factor
        self._watcher_thread = None
        self.poll_retry_delay = poll_retry_delay
        self._work_task: Optional[asyncio.Future] = None
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
        self._job_executors, self._job_pollers = [], []

        for task in self.tasks:
            jobs_queue: asyncio.Queue = asyncio.Queue()
            task_state = TaskState()

            poller = JobPoller(
                self.zeebe_adapter,
                task,
                jobs_queue,
                self.name,
                self.request_timeout,
                task_state,
                self.poll_retry_delay,
            )
            executor = JobExecutor(task, jobs_queue, task_state)
            self._job_pollers.append(poller)
            self._job_executors.append(executor)

        coroutines = [poller.poll() for poller in self._job_pollers] + [
            executor.execute() for executor in self._job_executors
        ]

        self._work_task = asyncio.gather(*coroutines)

        try:
            await self._work_task
        except asyncio.CancelledError:
            logger.info("Zeebe worker was stopped")
            return

    async def stop(self) -> None:
        """
        Stop the worker. This will emit a signal asking tasks to complete the current task and stop polling for new.
        """
        if self._work_task is not None:
            self._work_task.cancel()

        for poller in self._job_pollers:
            await poller.stop()

        for executor in self._job_executors:
            await executor.stop()

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
