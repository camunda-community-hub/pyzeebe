from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import anyio.abc
import grpc
import pytest

from pyzeebe import ExceptionHandler, TaskDecorator, ZeebeTaskRouter
from pyzeebe.errors import DuplicateTaskTypeError
from pyzeebe.job.job import Job, JobController
from pyzeebe.task.task import Task
from pyzeebe.worker.job_poller import JobPoller, JobStreamer
from pyzeebe.worker.worker import ZeebeWorker


@pytest.mark.anyio
class TestAddTask:
    async def test_add_task(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type) == task

    async def test_raises_on_duplicate(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)
        with pytest.raises(DuplicateTaskTypeError):
            zeebe_worker._add_task(task)

    async def test_only_one_task_added(self, zeebe_worker: ZeebeWorker):
        @zeebe_worker.task(str(uuid4()))
        def dummy_function():
            pass

        assert len(zeebe_worker.tasks) == 1

    async def test_task_type_saved(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type).type == task.type

    async def test_variables_to_fetch_match_function_parameters(self, zeebe_worker: ZeebeWorker, task_type: str):
        expected_variables_to_fetch = ["x"]

        @zeebe_worker.task(task_type)
        def dummy_function(x):
            pass

        assert zeebe_worker.get_task(task_type).config.variables_to_fetch == expected_variables_to_fetch


@pytest.mark.anyio
class TestDecorator:
    async def test_add_before_decorator(self, zeebe_worker: ZeebeWorker, decorator: TaskDecorator):
        zeebe_worker.before(decorator)
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    async def test_add_after_decorator(self, zeebe_worker: ZeebeWorker, decorator: TaskDecorator):
        zeebe_worker.after(decorator)
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after

    async def test_set_exception_handler(self, zeebe_worker: ZeebeWorker, exception_handler: ExceptionHandler):
        zeebe_worker.exception_handler(exception_handler)
        assert exception_handler is zeebe_worker._exception_handler

    async def test_add_constructor_before_decorator(self, aio_grpc_channel: grpc.aio.Channel, decorator: TaskDecorator):
        zeebe_worker = ZeebeWorker(aio_grpc_channel, before=[decorator])
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    async def test_add_constructor_after_decorator(self, aio_grpc_channel: grpc.aio.Channel, decorator: TaskDecorator):
        zeebe_worker = ZeebeWorker(aio_grpc_channel, after=[decorator])
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after

    async def test_set_constructor_exception_handler(
        self, aio_grpc_channel: grpc.aio.Channel, exception_handler: ExceptionHandler
    ):
        zeebe_worker = ZeebeWorker(aio_grpc_channel, exception_handler=exception_handler)
        assert exception_handler is zeebe_worker._exception_handler


@pytest.mark.anyio
class TestIncludeRouter:
    async def test_include_router_adds_task(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str):
        self.include_router_with_task(zeebe_worker, router, task_type)

        assert zeebe_worker.get_task(task_type) is not None

    async def test_include_multiple_routers(self, zeebe_worker: ZeebeWorker, routers: list[ZeebeTaskRouter]):
        for router in routers:
            self.include_router_with_task(zeebe_worker, router)

        assert len(zeebe_worker.tasks) == len(routers)

    async def test_router_before_decorator(
        self,
        zeebe_worker: ZeebeWorker,
        router: ZeebeTaskRouter,
        decorator: TaskDecorator,
        job: Job,
        job_controller: JobController,
    ):
        router.before(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        await task.job_handler(job, job_controller)

        decorator.assert_called_once()

    async def test_router_after_decorator(
        self,
        zeebe_worker: ZeebeWorker,
        router: ZeebeTaskRouter,
        decorator: TaskDecorator,
        job: Job,
        job_controller: JobController,
    ):
        router.after(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        await task.job_handler(job, job_controller)

        decorator.assert_called_once()

    async def test_router_with_exception_handler(
        self,
        zeebe_worker: ZeebeWorker,
        router: ZeebeTaskRouter,
        exception_handler: ExceptionHandler,
        job: Job,
        job_controller: JobController,
    ):
        router.exception_handler(exception_handler)
        task = self.include_router_with_task_error(zeebe_worker, router)

        await task.job_handler(job, job_controller)

        exception_handler.assert_called_once()

    async def test_worker_with_before_decorator(
        self,
        zeebe_worker: ZeebeWorker,
        router: ZeebeTaskRouter,
        decorator: TaskDecorator,
        job: Job,
        job_controller: JobController,
    ):
        zeebe_worker.before(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        await task.job_handler(job, job_controller)

        decorator.assert_called_once()

    async def test_worker_with_after_decorator(
        self,
        zeebe_worker: ZeebeWorker,
        router: ZeebeTaskRouter,
        decorator: TaskDecorator,
        job: Job,
        job_controller: JobController,
    ):
        zeebe_worker.after(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        await task.job_handler(job, job_controller)

        decorator.assert_called_once()

    async def test_worker_with_exception_handler(
        self,
        zeebe_worker: ZeebeWorker,
        router: ZeebeTaskRouter,
        exception_handler: ExceptionHandler,
        job: Job,
        job_controller: JobController,
    ):
        zeebe_worker.exception_handler(exception_handler)
        task = self.include_router_with_task_error(zeebe_worker, router)

        await task.job_handler(job, job_controller)

        exception_handler.assert_called_once()

    async def test_worker_and_router_with_exception_handler(
        self,
        zeebe_worker: ZeebeWorker,
        router: ZeebeTaskRouter,
        job: Job,
        job_controller: JobController,
    ):
        exception_handler_router = AsyncMock()
        exception_handler_worker = AsyncMock()
        router.exception_handler(exception_handler_router)
        zeebe_worker.exception_handler(exception_handler_worker)
        task = self.include_router_with_task_error(zeebe_worker, router)

        await task.job_handler(job, job_controller)

        exception_handler_router.assert_called_once()
        exception_handler_worker.assert_not_called()

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


@pytest.mark.anyio
class TestWorker:
    @pytest.fixture()
    def zeebe_worker(self, aio_grpc_channel_mock):
        return ZeebeWorker(grpc_channel=aio_grpc_channel_mock, stream_enabled=True)

    @staticmethod
    async def wait_for_channel_ready(*, task_status: anyio.abc.TaskStatus = anyio.TASK_STATUS_IGNORED):
        task_status.started()

    async def test_start_stop(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        await zeebe_worker.work()
        zeebe_worker._stop_event.wait.assert_awaited_once()

        await zeebe_worker.stop()
        zeebe_worker._stop_event.set.assert_called_once()

    async def test_poller_stoped(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._init_tasks = Mock()
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        poller_mock = AsyncMock(spec_set=JobPoller)
        zeebe_worker._job_pollers = [poller_mock]

        await zeebe_worker.work()
        poller_mock.poll.assert_awaited_once()

        await zeebe_worker.stop()
        poller_mock.stop.assert_awaited_once()

    async def test_poller_failed(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._init_tasks = Mock()

        poller_mock = AsyncMock(spec_set=JobPoller, poll=AsyncMock(side_effect=[Exception("test_exception")]))
        zeebe_worker._job_pollers = [poller_mock]

        with pytest.raises(Exception, match=r"unhandled errors in a TaskGroup"):
            await zeebe_worker.work()

        poller_mock.poll.assert_awaited_once()

    async def test_second_poller_should_cancel(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._init_tasks = Mock()

        poller2_cancel_event = anyio.Event()

        async def poll2():
            try:
                await anyio.Event().wait()
            except asyncio.CancelledError:
                poller2_cancel_event.set()

        poller_mock = AsyncMock(spec_set=JobPoller, poll=AsyncMock(side_effect=[Exception("test_exception")]))
        poller2_mock = AsyncMock(spec_set=JobPoller, poll=AsyncMock(wraps=poll2))
        zeebe_worker._job_pollers = [poller_mock, poller2_mock]

        with pytest.raises(Exception, match=r"unhandled errors in a TaskGroup"):
            await zeebe_worker.work()

        poller_mock.poll.assert_awaited_once()
        poller2_mock.poll.assert_awaited_once()
        assert poller2_cancel_event.is_set()

    async def test_streamer_stoped(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._init_tasks = Mock()
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        streamer_mock = AsyncMock(spec_set=JobStreamer)
        zeebe_worker._job_streamers = [streamer_mock]

        await zeebe_worker.work()
        streamer_mock.poll.assert_awaited_once()

        await zeebe_worker.stop()
        streamer_mock.stop.assert_awaited_once()

    async def test_streamer_failed(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._init_tasks = Mock()

        streamer_mock = AsyncMock(spec_set=JobStreamer, poll=AsyncMock(side_effect=[Exception("test_exception")]))
        zeebe_worker._job_streamers = [streamer_mock]

        with pytest.raises(Exception, match=r"unhandled errors in a TaskGroup"):
            await zeebe_worker.work()

        streamer_mock.poll.assert_awaited_once()
