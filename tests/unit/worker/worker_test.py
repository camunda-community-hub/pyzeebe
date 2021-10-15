from typing import List
from uuid import uuid4

import grpc
import pytest

from pyzeebe import TaskDecorator, ZeebeTaskRouter
from pyzeebe.errors import DuplicateTaskTypeError
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
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

        assert zeebe_worker.get_task(
            task_type).config.variables_to_fetch == expected_variables_to_fetch


class TestDecorator:
    def test_add_before_decorator(self, zeebe_worker: ZeebeWorker, decorator: TaskDecorator):
        zeebe_worker.before(decorator)
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    def test_add_after_decorator(self, zeebe_worker: ZeebeWorker, decorator: TaskDecorator):
        zeebe_worker.after(decorator)
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after

    def test_add_constructor_before_decorator(
        self, aio_grpc_channel: grpc.aio.Channel, decorator: TaskDecorator
    ):
        zeebe_worker = ZeebeWorker(aio_grpc_channel, before=[decorator])
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    def test_add_constructor_after_decorator(
        self, aio_grpc_channel: grpc.aio.Channel, decorator: TaskDecorator
    ):
        zeebe_worker = ZeebeWorker(aio_grpc_channel, after=[decorator])
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after


class TestIncludeRouter:
    def test_include_router_adds_task(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str):
        self.include_router_with_task(zeebe_worker, router, task_type)

        assert zeebe_worker.get_task(task_type) is not None

    def test_include_multiple_routers(self, zeebe_worker: ZeebeWorker, routers: List[ZeebeTaskRouter]):
        for router in routers:
            self.include_router_with_task(zeebe_worker, router)

        assert len(zeebe_worker.tasks) == len(routers)

    @pytest.mark.asyncio
    async def test_router_before_decorator(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter,
                                           decorator: TaskDecorator,
                                           mocked_job_with_adapter: Job):
        router.before(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        await task.job_handler(mocked_job_with_adapter)

        decorator.assert_called_once()

    @pytest.mark.asyncio
    async def test_router_after_decorator(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter,
                                          decorator: TaskDecorator,
                                          mocked_job_with_adapter: Job):
        router.after(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        await task.job_handler(mocked_job_with_adapter)

        decorator.assert_called_once()

    @staticmethod
    def include_router_with_task(zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str = None) -> Task:
        task_type = task_type or str(uuid4())

        @router.task(task_type)
        def dummy_function():
            return {}

        zeebe_worker.include_router(router)
        return zeebe_worker.get_task(task_type)
