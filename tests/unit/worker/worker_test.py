from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import anyio.abc
import pytest

from pyzeebe import ZeebeTaskRouter
from pyzeebe.job.job import Job, JobController
from pyzeebe.job.job_status import JobStatus
from pyzeebe.task.task import Task
from pyzeebe.worker.job_executor import JobExecutor
from pyzeebe.worker.job_poller import JobPoller
from pyzeebe.worker.worker import ZeebeWorker


class TestIncludeRouter:
    def test_include_router_adds_task(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str):
        self.include_router_with_task(zeebe_worker, router, task_type)

        assert zeebe_worker.get_task(task_type) is not None

    def test_include_multiple_routers(self, zeebe_worker: ZeebeWorker, routers: list[ZeebeTaskRouter]):
        for router in routers:
            self.include_router_with_task(zeebe_worker, router)

        assert len(zeebe_worker.router.tasks) == len(routers)

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
        return ZeebeWorker(grpc_channel=aio_grpc_channel_mock)

    @staticmethod
    async def wait_for_channel_ready(*, task_status: anyio.abc.TaskStatus = anyio.TASK_STATUS_IGNORED):
        task_status.started()

    async def test_start_stop(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        await zeebe_worker.work()
        zeebe_worker._stop_event.wait.assert_awaited_once()

        await zeebe_worker.stop()
        zeebe_worker._stop_event.set.assert_called_once()

    async def test_executor_stoped(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._init_tasks = Mock()
        zeebe_worker._stop_event = AsyncMock(spec_set=anyio.Event)

        executor_mock = AsyncMock(spec_set=JobExecutor)
        zeebe_worker._job_executors = [executor_mock]

        await zeebe_worker.work()
        executor_mock.execute.assert_awaited_once()

        await zeebe_worker.stop()
        executor_mock.stop.assert_awaited_once()

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

        with pytest.raises(Exception, match=r"unhandled errors in a TaskGroup \(1 sub-exception\)"):
            await zeebe_worker.work()

        poller_mock.poll.assert_awaited_once()

    async def test_second_poller_should_cancel(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._init_tasks = Mock()

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

    def test_init_tasks(self, zeebe_worker: ZeebeWorker, task_type):
        @zeebe_worker.task(task_type)
        def dummy_function():
            pass

        assert zeebe_worker._job_executors == []
        assert zeebe_worker._job_pollers == []

        zeebe_worker._init_tasks()

        assert len(zeebe_worker._job_executors) == 1
        assert zeebe_worker._job_executors[0].task.type == task_type

        assert len(zeebe_worker._job_pollers) == 1
        assert zeebe_worker._job_pollers[0].task.type == task_type


class TestTask:
    def test_task_added(self, zeebe_worker: ZeebeWorker):
        @zeebe_worker.task(str(uuid4()))
        def dummy_function():
            pass

        assert len(zeebe_worker.router.tasks) == 1

    def test_get_task(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker.router.tasks.append(task)

        found_task = zeebe_worker.get_task(task.type)

        assert found_task == task

    def test_remove_task(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker.router.tasks.append(task)

        assert task in zeebe_worker.router.tasks

        zeebe_worker.remove_task(task.type)

        assert task not in zeebe_worker.router.tasks


class TestMiddleware:
    def test_add_middleware(self, zeebe_worker: ZeebeWorker):
        middleware_cls_mock = Mock()

        assert len(zeebe_worker.middlewares) == 0

        zeebe_worker.add_middleware(middleware_cls_mock, foo="bar")

        assert len(zeebe_worker.middlewares) == 1
        assert zeebe_worker.middlewares[0].cls == middleware_cls_mock
        assert zeebe_worker.middlewares[0].options == {"foo": "bar"}

    async def test_middleware_in_job_handler(
        self, zeebe_worker: ZeebeWorker, task: Task, job: Job, job_controller: JobController
    ):
        order = []

        async def middleware_1(job, job_controller, task, call_next):
            order.append(1)
            await call_next(job, job_controller)
            order.append(1)

        async def middleware_2(job, job_controller, task, call_next):
            order.append(2)
            await call_next(job, job_controller)
            order.append(2)

        middleware_cls_mock_1 = Mock(return_value=middleware_1)
        middleware_cls_mock_2 = Mock(return_value=middleware_2)

        assert len(zeebe_worker.middlewares) == 0

        zeebe_worker.add_middleware(middleware_cls_mock_1)
        zeebe_worker.add_middleware(middleware_cls_mock_2)

        job_handler = zeebe_worker._build_middleware_stack(task)

        await job_handler(job, job_controller)

        assert order == [2, 1, 1, 2]

    async def test_middleware_order(
        self, zeebe_worker: ZeebeWorker, task: Task, job: Job, job_controller: JobController
    ):
        middleware_mock = AsyncMock()
        middleware_cls_mock = Mock(return_value=middleware_mock)

        assert len(zeebe_worker.middlewares) == 0

        zeebe_worker.add_middleware(middleware_cls_mock, foo="bar")

        job_handler = zeebe_worker._build_middleware_stack(task)

        await job_handler(job, job_controller)

        middleware_mock.assert_awaited_once()

    async def test_job_status_changed(
        self, zeebe_worker: ZeebeWorker, task: Task, job: Job, job_controller: JobController
    ):
        status = None

        async def middleware_mock(job, job_controller, task, call_next):
            nonlocal status
            await call_next(job, job_controller)
            status = job.status

        middleware_cls_mock = Mock(return_value=middleware_mock)

        assert len(zeebe_worker.middlewares) == 0

        zeebe_worker.add_middleware(middleware_cls_mock, foo="bar")

        job_handler = zeebe_worker._build_middleware_stack(task)

        await job_handler(job, job_controller)

        assert status == JobStatus.RunningAfterDecorators


class TestExceptionHandler:
    def test_add_exception_handler(self, zeebe_worker: ZeebeWorker):
        exception_handler_mock = Mock()

        assert len(zeebe_worker.exception_handlers) == 0

        zeebe_worker.add_exception_handler(Exception, exception_handler_mock)

        assert len(zeebe_worker.exception_handlers) == 1
        assert zeebe_worker.exception_handlers[Exception] == exception_handler_mock

    async def test_exception_handler_in_job_handler(
        self, zeebe_worker: ZeebeWorker, task: Task, job: Job, job_controller: JobController
    ):
        exception_handler_mock = AsyncMock()
        exception = Exception("some error")

        zeebe_worker.add_exception_handler(Exception, exception_handler_mock)

        task.job_handler = AsyncMock(side_effect=[exception])

        job_handler = zeebe_worker._build_middleware_stack(task)

        await job_handler(job, job_controller)

        exception_handler_mock.assert_awaited_once_with(exception, job, job_controller)

    @patch("pyzeebe.worker.worker.default_exception_handler")
    async def test_default_exception_handler_in_job_handler(
        self,
        default_exception_handler_mock,
        zeebe_worker: ZeebeWorker,
        task: Task,
        job: Job,
        job_controller: JobController,
    ):
        exception = Exception("some error")

        task.job_handler = AsyncMock(side_effect=[exception])

        job_handler = zeebe_worker._build_middleware_stack(task)

        await job_handler(job, job_controller)

        default_exception_handler_mock.assert_awaited_once_with(exception, job, job_controller)
