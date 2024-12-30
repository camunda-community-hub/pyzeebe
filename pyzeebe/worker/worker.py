from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Iterable, Mapping, Sequence
from functools import partial
from typing import Any, Callable, Literal, Optional, TypeVar, overload

import anyio
import grpc
from typing_extensions import ParamSpec

from pyzeebe.function_tools import Function
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.middlewares import Middleware
from pyzeebe.middlewares.base import CatchErrorMiddleware, ResponseMiddleware
from pyzeebe.task.exception_handler import default_exception_handler
from pyzeebe.task.task import Task
from pyzeebe.types import ExceptionHandler, JobHandler, MiddlewareProto
from pyzeebe.worker.job_executor import JobExecutor
from pyzeebe.worker.job_poller import JobPoller
from pyzeebe.worker.task_router import ZeebeTaskRouter
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")
RD = TypeVar("RD", bound=Optional[dict[str, Any]])


class ZeebeWorker:
    """A zeebe worker that can connect to a zeebe instance and perform tasks."""

    def __init__(
        self,
        grpc_channel: grpc.aio.Channel,
        name: str | None = None,
        request_timeout: int = 0,
        max_connection_retries: int = 10,
        poll_retry_delay: int = 5,
        tenant_ids: list[str] | None = None,
        middlewares: Sequence[Middleware] | None = None,
        exception_handlers: Mapping[type[Exception], ExceptionHandler] | None = None,
    ):
        """
        Args:
            grpc_channel (grpc.aio.Channel): GRPC Channel connected to a Zeebe gateway
            name (str): Name of zeebe worker
            request_timeout (int): Longpolling timeout for getting tasks from zeebe. If 0 default value is used
            middlewares (Sequence[Middleware] | None): Middlewares to be performed before and after each task
            exception_handlers (Mapping[type[Exception], ExceptionHandler] | None): Handlers that will be called when a job fails.
                If none of exception handlers were added, then :py:func:`default_exception_handler` will used for :py:class:`Exception`.
            max_connection_retries (int): Amount of connection retries before worker gives up on connecting to zeebe. To setup with infinite retries use -1
            poll_retry_delay (int): The number of seconds to wait before attempting to poll again when reaching max amount of running jobs
            tenant_ids (list[str]): A list of tenant IDs for which to activate jobs. New in Zeebe 8.3.
        """
        self.zeebe_adapter = ZeebeAdapter(grpc_channel, max_connection_retries)
        self.name = name or socket.gethostname()
        self.request_timeout = request_timeout
        self.poll_retry_delay = poll_retry_delay
        self.tenant_ids = tenant_ids
        self.middlewares: list[Middleware] = list(middlewares) if middlewares else []
        self.exception_handlers: dict[type[Exception], ExceptionHandler] = (
            dict(exception_handlers) if exception_handlers else {}
        )
        self.router = ZeebeTaskRouter()

        self._job_pollers: list[JobPoller] = []
        self._job_executors: list[JobExecutor] = []
        self._stop_event = anyio.Event()
        self._started = False

    def add_middleware(
        self,
        middleware_class: type[MiddlewareProto],
        **options: Any,
    ) -> None:
        """
        Add middleware to worker.

        Args:
            middleware_class (type[MiddlewareProto]): Middleware class (or factory).
            options (Any): Options for middleware, will passed to constructor.

        Raises:
            ValueError: If the worker has already started.
        """
        if self._started is True:
            raise ValueError("It isn't possible to add middleware to started worker.")
        self.middlewares.insert(0, Middleware(middleware_class, **options))

    def add_exception_handler(
        self,
        exc_class: type[Exception],
        handler: ExceptionHandler,
    ) -> None:
        """
        Add exception handler to worker. If none of exception handlers were added, then :py:func:`default_exception_handler` will used for :py:class:`Exception`.

        Args:
            exc_class (type[Exception]): Class of exception, that will handle.
            handler (ExceptionHandler): Handler for this exception.

        Raises:
            ValueError: If the worker has already started.
        """
        if self._started is True:
            raise ValueError("It isn't possible to add exception handler to started worker.")
        self.exception_handlers[exc_class] = handler

    def _build_middleware_stack(self, task: Task) -> JobHandler:
        callable = task.job_handler

        middlewares = (
            [
                Middleware(
                    ResponseMiddleware,
                    exception_handlers=(
                        self.exception_handlers if self.exception_handlers else {Exception: default_exception_handler}
                    ),
                )
            ]
            + self.middlewares
            + [Middleware(CatchErrorMiddleware)]
        )
        for middleware in reversed(middlewares):
            mld = middleware.cls(**middleware.options)
            callable = partial(mld, task=task, call_next=callable)

        return callable

    @overload
    def task(
        self,
        task_type: str,
        variables_to_fetch: Iterable[str] | None = None,
        timeout_ms: int = 10000,
        max_jobs_to_activate: int = 32,
        max_running_jobs: int = 32,
        *,
        single_value: Literal[False] = False,
    ) -> Callable[[Function[P, RD]], Function[P, RD]]: ...

    @overload
    def task(
        self,
        task_type: str,
        variables_to_fetch: Iterable[str] | None = None,
        timeout_ms: int = 10000,
        max_jobs_to_activate: int = 32,
        max_running_jobs: int = 32,
        *,
        single_value: Literal[True],
        variable_name: str,
    ) -> Callable[[Function[P, R]], Function[P, R]]: ...

    def task(
        self,
        task_type: str,
        variables_to_fetch: Iterable[str] | None = None,
        timeout_ms: int = 10000,
        max_jobs_to_activate: int = 32,
        max_running_jobs: int = 32,
        single_value: bool = False,
        variable_name: str | None = None,
    ) -> Callable[[Function[P, R]], Function[P, R]]:
        return self.router.task(  # type: ignore[call-overload,no-any-return]
            task_type=task_type,
            variables_to_fetch=variables_to_fetch,
            timeout_ms=timeout_ms,
            max_jobs_to_activate=max_jobs_to_activate,
            max_running_jobs=max_running_jobs,
            single_value=single_value,
            variable_name=variable_name,
        )

    task.__doc__ = ZeebeTaskRouter.task.__doc__

    def remove_task(self, task_type: str) -> Task:
        return self.router.remove_task(task_type)

    remove_task.__doc__ = ZeebeTaskRouter.remove_task.__doc__

    def get_task(self, task_type: str) -> Task:
        return self.router.get_task(task_type)

    get_task.__doc__ = ZeebeTaskRouter.get_task.__doc__

    def include_router(self, *routers: ZeebeTaskRouter) -> None:
        self.router.include_router(*routers)

    include_router.__doc__ = ZeebeTaskRouter.include_router.__doc__

    def _init_tasks(self) -> None:
        self._job_executors, self._job_pollers = [], []

        for task in self.router.tasks:
            jobs_queue = asyncio.Queue[Job]()
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
            executor = JobExecutor(
                task,
                jobs_queue,
                task_state,
                self.zeebe_adapter,
                self._build_middleware_stack(task),
            )

            self._job_pollers.append(poller)
            self._job_executors.append(executor)

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
        self._started = True
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
        self._started = False
