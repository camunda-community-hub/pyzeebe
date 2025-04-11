from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Mapping, Sequence

import anyio
import grpc

from pyzeebe.grpc_internals.types import HealthCheckResponse
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.middlewares import BaseMiddleware, ExceptionMiddleware
from pyzeebe.task.exception_handler import ExceptionHandler, default_exception_handler
from pyzeebe.worker.job_executor import JobExecutor
from pyzeebe.worker.job_poller import JobPoller, JobStreamer
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
        max_connection_retries: int = 10,
        poll_retry_delay: int = 5,
        tenant_ids: list[str] | None = None,
        stream_enabled: bool = False,
        stream_request_timeout: int = 3600,
        middlewares: Sequence[BaseMiddleware] | None = None,
        exception_handlers: Mapping[type[Exception], ExceptionHandler] | None = None,
    ):
        """
        Args:
            grpc_channel (grpc.aio.Channel): GRPC Channel connected to a Zeebe gateway
            name (str): Name of zeebe worker
            request_timeout (int): Longpolling timeout for getting tasks from zeebe. If 0 default value is used
            middlewares (list[BaseMiddleware] | None): Middlewares to be performed before and after each task
            exception_handlers (dict[type[Exception], ExceptionHandler] | None): Handlers that will be called when a job fails.
                If none of exception handlers were added, then :py:func:`default_exception_handler` will used for :py:class:`Exception`.
            max_connection_retries (int): Amount of connection retries before worker gives up on connecting to zeebe. To setup with infinite retries use -1
            poll_retry_delay (int): The number of seconds to wait before attempting to poll again when reaching max amount of running jobs
            tenant_ids (list[str]): A list of tenant IDs for which to activate jobs. New in Zeebe 8.3.
            stream_enabled (bool): Enables the job worker to stream jobs. It will still poll for older jobs, but streaming is favored. New in Zeebe 8.4.
            stream_request_timeout (int): If streaming is enabled, this sets the timeout on the underlying job stream.
                It's useful to set a few hours to load-balance your streams over time. New in Zeebe 8.4.
        """
        super().__init__()
        self.zeebe_adapter = ZeebeAdapter(grpc_channel, max_connection_retries)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.poll_retry_delay = poll_retry_delay
        self.tenant_ids = tenant_ids
        self._job_pollers: list[JobPoller] = []
        self._job_streamers: list[JobStreamer] = []
        self._job_executors: list[JobExecutor] = []
        self._stop_event = anyio.Event()
        self._stream_enabled = stream_enabled
        self._stream_request_timeout = stream_request_timeout
        self.user_middlewares: list[BaseMiddleware] = list(middlewares) if middlewares is not None else []
        self.middlewares: list[BaseMiddleware] | None = None
        self.exception_handlers: dict[type[Exception], ExceptionHandler] = (
            (dict(exception_handlers)) if exception_handlers is not None else {}
        )

    def _setup(self) -> None:
        self._build_middleware_stack()
        self._init_tasks()

    def _init_tasks(self) -> None:
        assert self.middlewares is not None

        self._job_executors, self._job_pollers, self._job_streamers = [], [], []

        for task in self.tasks:
            jobs_queue = asyncio.Queue[Job]()
            task_state = TaskState()

            poller = JobPoller(
                zeebe_adapter=self.zeebe_adapter,
                task=task,
                queue=jobs_queue,
                worker_name=self.name,
                request_timeout=self.request_timeout,
                task_state=task_state,
                poll_retry_delay=self.poll_retry_delay,
                tenant_ids=self.tenant_ids,
                middlewares=self.middlewares,
            )
            executor = JobExecutor(
                task=task,
                jobs=jobs_queue,
                task_state=task_state,
                zeebe_adapter=self.zeebe_adapter,
                middlewares=self.middlewares,
            )

            self._job_pollers.append(poller)
            self._job_executors.append(executor)

            if self._stream_enabled:
                streamer = JobStreamer(
                    zeebe_adapter=self.zeebe_adapter,
                    task=task,
                    queue=jobs_queue,
                    worker_name=self.name,
                    stream_request_timeout=self._stream_request_timeout,
                    task_state=task_state,
                    tenant_ids=self.tenant_ids,
                    middlewares=self.middlewares,
                )
                self._job_streamers.append(streamer)

    def _build_middleware_stack(self) -> None:
        self.middlewares = self.user_middlewares.copy()

        if Exception not in self.exception_handlers:
            self.exception_handlers[Exception] = default_exception_handler

        self.middlewares.append(ExceptionMiddleware(self.exception_handlers))

    async def work(self) -> None:
        """
        Start the worker. The worker will poll zeebe for jobs of each task in a different asyncio task.

        Raises:
            ActivateJobsRequestInvalidError: If one of the worker's task has invalid types
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error
            UnknownGrpcStatusCodeError: If Zeebe returns an unexpected status code

        """
        self._setup()

        async with anyio.create_task_group() as tg:
            for poller in self._job_pollers:
                tg.start_soon(poller.poll)

            for streamer in self._job_streamers:
                tg.start_soon(streamer.poll)

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

        for streamer in self._job_streamers:
            await streamer.stop()

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
                self._add_task(task)

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """
        Add middleware to worker.

        Args:
            middleware_class (type[MiddlewareProto]): Middleware.

        Raises:
            RuntimeError: If the worker has already started.
        """
        if self.middlewares is not None:
            raise RuntimeError("It isn't possible to add middleware to started worker.")
        self.user_middlewares.insert(0, middleware)

    def add_exception_handler(self, exc_class: type[Exception], handler: ExceptionHandler) -> None:
        """
        Add exception handler to worker. If none of exception handlers were added, then :py:func:`default_exception_handler` will used for :py:class:`Exception`.

        Args:
            exc_class (type[Exception]): Class of exception, that will handle.
            handler (ExceptionHandler): Handler for this exception.

        Raises:
            RuntimeError: If the worker has already started.
        """
        if self.middlewares is not None:
            raise RuntimeError("It isn't possible to add exception handler to started worker.")
        self.exception_handlers[exc_class] = handler

    async def healthcheck(self) -> HealthCheckResponse:
        """Ping Zeebe Gateway using GRPC Health Checking Protocol."""
        return await self.zeebe_adapter.healthcheck()
