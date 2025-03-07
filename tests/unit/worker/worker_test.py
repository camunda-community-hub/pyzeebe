from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import anyio.abc
import grpc
import pytest

from pyzeebe import ZeebeTaskRouter
from pyzeebe.errors import DuplicateTaskTypeError
from pyzeebe.middlewares import BaseMiddleware, ExceptionMiddleware
from pyzeebe.task.exception_handler import ExceptionHandler, default_exception_handler
from pyzeebe.task.task import Task
from pyzeebe.worker.job_poller import JobPoller, JobStreamer
from pyzeebe.worker.worker import ZeebeWorker


class TestAddTask:
    def test_add_task(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type) == task

    def test_raises_on_duplicate(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)
        with pytest.raises(DuplicateTaskTypeError):
            zeebe_worker._add_task(task)

    def test_only_one_task_added(self, zeebe_worker: ZeebeWorker):
        @zeebe_worker.task(str(uuid4()))
        def dummy_function():
            pass

        assert len(zeebe_worker.tasks) == 1

    def test_task_type_saved(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type).type == task.type

    def test_variables_to_fetch_match_function_parameters(self, zeebe_worker: ZeebeWorker, task_type: str):
        expected_variables_to_fetch = ["x"]

        @zeebe_worker.task(task_type)
        def dummy_function(x):
            pass

        assert zeebe_worker.get_task(task_type).config.variables_to_fetch == expected_variables_to_fetch


class TestAddMiddleware:
    @pytest.fixture
    def middleware(self):
        return AsyncMock(spec_set=BaseMiddleware)

    def test_add_middleware(self, zeebe_worker: ZeebeWorker, middleware: BaseMiddleware):
        zeebe_worker.add_middleware(middleware)

        assert middleware in zeebe_worker.user_middlewares

    def test_add_middleware_worker_already_started(self, zeebe_worker: ZeebeWorker, middleware: BaseMiddleware):
        zeebe_worker._build_middleware_stack()

        with pytest.raises(RuntimeError, match="It isn't possible to add middleware to started worker."):
            zeebe_worker.add_middleware(middleware)

    def test_middleware_in_middleware_stack(self, zeebe_worker: ZeebeWorker, middleware: BaseMiddleware):
        zeebe_worker.add_middleware(middleware)
        zeebe_worker._build_middleware_stack()

        assert middleware in zeebe_worker.middlewares

    def test_middleware_order(self, zeebe_worker: ZeebeWorker, middleware: BaseMiddleware):
        zeebe_worker.add_middleware(middleware)
        zeebe_worker._build_middleware_stack()

        assert len(zeebe_worker.middlewares) == 2
        assert zeebe_worker.middlewares[0] is middleware
        assert isinstance(zeebe_worker.middlewares[1], ExceptionMiddleware)  # default middleware


class TestAddExceptionHandler:
    @pytest.fixture
    def exception_handler(self):
        return AsyncMock()

    def test_add_exception_handler(self, zeebe_worker: ZeebeWorker, exception_handler: ExceptionHandler):
        zeebe_worker.add_exception_handler(Exception, exception_handler)

        assert zeebe_worker.exception_handlers.get(Exception) is exception_handler

    def test_add_exception_handler_worker_already_started(
        self, zeebe_worker: ZeebeWorker, exception_handler: ExceptionHandler
    ):
        zeebe_worker._build_middleware_stack()

        with pytest.raises(RuntimeError, match="It isn't possible to add exception handler to started worker."):
            zeebe_worker.add_exception_handler(Exception, exception_handler)

    def test_exception_handler_in_middleware_stack(
        self, zeebe_worker: ZeebeWorker, exception_handler: ExceptionHandler
    ):
        zeebe_worker.add_exception_handler(Exception, exception_handler)
        zeebe_worker._build_middleware_stack()

        assert len(zeebe_worker.middlewares) == 1
        assert isinstance(zeebe_worker.middlewares[0], ExceptionMiddleware)
        assert len(zeebe_worker.middlewares[0].exception_handlers) == 1
        assert zeebe_worker.middlewares[0].exception_handlers[Exception] is exception_handler

    def test_default_exception_handler_in_middleware_stack(
        self, zeebe_worker: ZeebeWorker, exception_handler: ExceptionHandler
    ):
        zeebe_worker.add_exception_handler(ValueError, exception_handler)
        zeebe_worker._build_middleware_stack()

        assert len(zeebe_worker.middlewares) == 1
        assert isinstance(zeebe_worker.middlewares[0], ExceptionMiddleware)
        assert len(zeebe_worker.middlewares[0].exception_handlers) == 2
        assert zeebe_worker.middlewares[0].exception_handlers[Exception] is default_exception_handler
        assert zeebe_worker.middlewares[0].exception_handlers[ValueError] is exception_handler


class TestIncludeRouter:
    def test_include_router_adds_task(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str):
        self.include_router_with_task(zeebe_worker, router, task_type)

        assert zeebe_worker.get_task(task_type) is not None

    def test_include_multiple_routers(self, zeebe_worker: ZeebeWorker, routers: list[ZeebeTaskRouter]):
        for router in routers:
            self.include_router_with_task(zeebe_worker, router)

        assert len(zeebe_worker.tasks) == len(routers)

    @staticmethod
    def include_router_with_task(zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str = None) -> Task:
        task_type = task_type or str(uuid4())

        @router.task(task_type)
        def dummy_function():
            return {}

        zeebe_worker.include_router(router)
        return zeebe_worker.get_task(task_type)

    @staticmethod
    def include_router_with_task_error(
        zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str = None
    ) -> Task:
        task_type = task_type or str(uuid4())

        @router.task(task_type)
        def dummy_function():
            raise Exception()

        zeebe_worker.include_router(router)
        return zeebe_worker.get_task(task_type)


class TestWorker:
    @pytest.fixture()
    def zeebe_worker(self, aio_grpc_channel_mock):
        return ZeebeWorker(grpc_channel=aio_grpc_channel_mock, stream_enabled=True)

    @staticmethod
    async def wait_for_channel_ready(*, task_status: anyio.abc.TaskStatus = anyio.TASK_STATUS_IGNORED):
        task_status.started()

    async def test_setup_without_stream(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._stream_enabled = False
        zeebe_worker._add_task(task)

        zeebe_worker._setup()

        assert len(zeebe_worker._job_executors) == 1
        assert len(zeebe_worker._job_pollers) == 1
        assert len(zeebe_worker._job_streamers) == 0

    async def test_setup_with_stream(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._stream_enabled = True
        zeebe_worker._add_task(task)

        zeebe_worker._setup()

        assert len(zeebe_worker._job_executors) == 1
        assert len(zeebe_worker._job_pollers) == 1
        assert len(zeebe_worker._job_streamers) == 1

    async def test_start_stop(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        await zeebe_worker.work()
        zeebe_worker._stop_event.wait.assert_awaited_once()

        await zeebe_worker.stop()
        zeebe_worker._stop_event.set.assert_called_once()

    async def test_poller_stoped(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._setup = Mock()
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        poller_mock = AsyncMock(spec_set=JobPoller)
        zeebe_worker._job_pollers = [poller_mock]

        await zeebe_worker.work()
        poller_mock.poll.assert_awaited_once()

        await zeebe_worker.stop()
        poller_mock.stop.assert_awaited_once()

    async def test_poller_failed(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._setup = Mock()

        poller_mock = AsyncMock(spec_set=JobPoller, poll=AsyncMock(side_effect=[Exception("test_exception")]))
        zeebe_worker._job_pollers = [poller_mock]

        with pytest.raises(Exception, match=r"unhandled errors in a TaskGroup \(1 sub-exception\)"):
            await zeebe_worker.work()

        poller_mock.poll.assert_awaited_once()

    async def test_second_poller_should_cancel(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._setup = Mock()

        poller2_cancel_event = asyncio.Event()

        async def poll2():
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                poller2_cancel_event.set()

        poller_mock = AsyncMock(spec_set=JobPoller, poll=AsyncMock(side_effect=[Exception("test_exception")]))
        poller2_mock = AsyncMock(spec_set=JobPoller, poll=AsyncMock(wraps=poll2))
        zeebe_worker._job_pollers = [poller_mock, poller2_mock]

        with pytest.raises(Exception, match=r"unhandled errors in a TaskGroup \(1 sub-exception\)"):
            await zeebe_worker.work()

        poller_mock.poll.assert_awaited_once()
        poller2_mock.poll.assert_awaited_once()
        assert poller2_cancel_event.is_set()

    async def test_streamer_stoped(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._setup = Mock()
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        streamer_mock = AsyncMock(spec_set=JobStreamer)
        zeebe_worker._job_streamers = [streamer_mock]

        await zeebe_worker.work()
        streamer_mock.poll.assert_awaited_once()

        await zeebe_worker.stop()
        streamer_mock.stop.assert_awaited_once()

    async def test_streamer_failed(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._setup = Mock()

        streamer_mock = AsyncMock(spec_set=JobStreamer, poll=AsyncMock(side_effect=[Exception("test_exception")]))
        zeebe_worker._job_streamers = [streamer_mock]

        with pytest.raises(Exception, match=r"unhandled errors in a TaskGroup \(1 sub-exception\)"):
            await zeebe_worker.work()

        streamer_mock.poll.assert_awaited_once()
