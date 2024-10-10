from __future__ import annotations

import asyncio
import logging
import socket

import anyio
import grpc

from pyzeebe import TaskDecorator
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.task import task_builder
from pyzeebe.task.exception_handler import ExceptionHandler
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
        name: str | None = None,
        request_timeout: int = 0,
        before: list[TaskDecorator] | None = None,
        after: list[TaskDecorator] | None = None,
        max_connection_retries: int = 10,
        poll_retry_delay: int = 5,
        tenant_ids: list[str] | None = None,
        exception_handler: ExceptionHandler | None = None,
    ):
        """
        Args:
            grpc_channel (grpc.aio.Channel): GRPC Channel connected to a Zeebe gateway
            name (str): Name of zeebe worker
            request_timeout (int): Longpolling timeout for getting tasks from zeebe. If 0 default value is used
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
            exception_handler (ExceptionHandler): Handler that will be called when a job fails.
            max_connection_retries (int): Amount of connection retries before worker gives up on connecting to zeebe. To setup with infinite retries use -1
            poll_retry_delay (int): The number of seconds to wait before attempting to poll again when reaching max amount of running jobs
            tenant_ids (List[str]): A list of tenant IDs for which to activate jobs. New in Zeebe 8.3.
        """
        super().__init__(before, after, exception_handler)
        self.zeebe_adapter = ZeebeAdapter(grpc_channel, max_connection_retries)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.poll_retry_delay = poll_retry_delay
        self.tenant_ids = tenant_ids
        self._job_pollers: list[JobPoller] = []
        self._job_executors: list[JobExecutor] = []
        self._stop_event = anyio.Event()

    def _init_tasks(self) -> None:
        self._job_executors, self._job_pollers = [], []

        for task in self.tasks:
            jobs_queue: asyncio.Queue[Job] = asyncio.Queue()
            task_state = TaskState()

            poller = JobPoller(
                self.zeebe_adapter,
                task,
                jobs_queue,
                self.name,
                self.request_timeout,
                task_state,
                self.poll_retry_delay,
                self.tenant_ids,
            )
            executor = JobExecutor(task, jobs_queue, task_state, self.zeebe_adapter)

            self._job_pollers.append(poller)
            self._job_executors.append(executor)

    async def work(self) -> None:
        """
        Start the worker. The worker will poll zeebe for jobs of each task in a different thread.

        Raises:
            ActivateJobsRequestInvalidError: If one of the worker's task has invalid types
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error
            UnknownGrpcStatusCodeError: If Zeebe returns an unexpected status code

        """
        self._init_tasks()

        async with anyio.create_task_group() as tg:
            for poller in self._job_pollers:
                tg.start_soon(poller.poll)

            for executor in self._job_executors:
                tg.start_soon(executor.execute)

            await self._stop_event.wait()

            tg.cancel_scope.cancel()

        logger.info("Zeebe worker was stopped")

    async def stop(self) -> None:
        """
        Stop the worker. This will emit a signal asking tasks to complete the current task and stop polling for new.
        """
        for poller in self._job_pollers:
            await poller.stop()

        for executor in self._job_executors:
            await executor.stop()

        self._stop_event.set()

    def include_router(self, *routers: ZeebeTaskRouter) -> None:
        """
        Adds all router's tasks to the worker.

        Raises:
            DuplicateTaskTypeError: If a task from the router already exists in the worker

        """
        for router in routers:
            for task in router.tasks:
                config_with_decorators = self._add_decorators_to_config(task.config)
                task = task_builder.build_task(task.original_function, config_with_decorators)
                self._add_task(task)
