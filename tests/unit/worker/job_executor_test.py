import asyncio
import json
from unittest.mock import AsyncMock, Mock

import pytest

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job, JobController
from pyzeebe.middlewares import (
    BaseMiddleware,
    ExceptionMiddleware,
    ExecuteMiddlewareStack,
)
from pyzeebe.task.exception_handler import default_exception_handler
from pyzeebe.task.task import Task
from pyzeebe.worker.job_executor import JobExecutor, create_job_callback
from pyzeebe.worker.task_state import TaskState


@pytest.fixture
def job_executor(task: Task, queue: asyncio.Queue, task_state: TaskState, zeebe_adapter: ZeebeAdapter):
    return JobExecutor(
        task=task,
        jobs=queue,
        task_state=task_state,
        zeebe_adapter=zeebe_adapter,
        middlewares=[ExceptionMiddleware({Exception: default_exception_handler})],
    )


@pytest.fixture(autouse=True)
def mock_job_handler(task: Task):
    task.job_handler = AsyncMock()


@pytest.mark.asyncio
class TestExecuteOneJob:
    async def test_executes_jobs(self, job_executor: JobExecutor, task: Task, job_controller: JobController):
        await job_executor.execute_one_job(job_controller)

        task.job_handler.assert_called_with(job_controller.job, job_controller)

    async def test_continues_on_deactivated_job(self, job_executor: JobExecutor, job_controller: JobController):
        await job_executor.execute_one_job(job_controller)
        await job_executor.execute_one_job(job_controller)

    async def test_executes_jobs_success(
        self, job_executor: JobExecutor, task: Task, mocked_job_controller: JobController
    ):
        task.job_handler.return_value = Mock(task_result="task_result")

        await job_executor.execute_one_job(mocked_job_controller)

        mocked_job_controller.set_success_status.assert_called_with("task_result")

    async def test_executes_jobs_error(
        self, job_executor: JobExecutor, task: Task, mocked_job_controller: JobController
    ):
        task.job_handler.side_effect = ValueError("test")

        await job_executor.execute_one_job(mocked_job_controller)

        mocked_job_controller.set_failure_status.assert_called_with("Failed job. Error: test")

    async def test_executes_middleware_order(
        self,
        task: Task,
        queue: asyncio.Queue,
        task_state: TaskState,
        zeebe_adapter: ZeebeAdapter,
        mocked_job_controller: JobController,
    ):
        order = []

        class Middleware(BaseMiddleware):
            def __init__(self, order: int) -> None:
                self.order = order

            async def execute_scope(
                self, call_next: ExecuteMiddlewareStack, job: Job, job_controller: JobController
            ) -> Job:
                order.append(self.order)
                result = await call_next(job, job_controller)
                order.append(self.order)
                return result

        job_executor = JobExecutor(
            task=task,
            jobs=queue,
            task_state=task_state,
            zeebe_adapter=zeebe_adapter,
            middlewares=[Middleware(0), Middleware(1)],
        )

        await job_executor.execute_one_job(mocked_job_controller)

        assert order == [1, 0, 0, 1]


@pytest.mark.asyncio
class TestGetNextJob:
    async def test_returns_expected_job(self, job_executor: JobExecutor, job_from_task: Job):
        await job_executor.jobs.put(job_from_task)

        assert await job_executor.get_next_job() == job_from_task


class TestShouldExecute:
    def test_returns_true_on_default(self, job_executor: JobExecutor):
        assert job_executor.should_execute()

    @pytest.mark.asyncio
    async def test_returns_false_when_executor_is_stopped(self, job_executor: JobExecutor):
        await job_executor.stop()

        assert not job_executor.should_execute()


@pytest.mark.asyncio
class TestStop:
    async def test_stops_executor(self, job_executor: JobExecutor):
        await job_executor.stop()

        await job_executor.execute()  # Implicitly test that execute returns immediately


class TestCreateJobCallback:
    def test_returns_callable(self, job_executor: JobExecutor, job_from_task: Job):
        callback = create_job_callback(job_executor, job_from_task)

        assert callable(callback)

    def test_signals_that_job_is_done(self, job_executor: JobExecutor, job_from_task: Job):
        task_done_mock = Mock()
        remove_from_task_state_mock = Mock()
        job_executor.jobs.task_done = task_done_mock
        job_executor.task_state.remove = remove_from_task_state_mock

        callback = create_job_callback(job_executor, job_from_task)
        callback(asyncio.Future())

        task_done_mock.assert_called_once()
        remove_from_task_state_mock.assert_called_once_with(job_from_task)

    def test_signals_that_job_is_done_with_exception(
        self, job_executor: JobExecutor, job_from_task: Job, caplog: pytest.LogCaptureFixture
    ):
        task_done_mock = Mock()
        remove_from_task_state_mock = Mock()
        job_executor.jobs.task_done = task_done_mock
        job_executor.task_state.remove = remove_from_task_state_mock

        callback = create_job_callback(job_executor, job_from_task)

        exception = None
        try:
            json.dumps({"foo": object})
        except TypeError as err:
            exception = err

        assert exception

        fut = asyncio.Future()
        fut.set_exception(exception)
        callback(fut)

        task_done_mock.assert_called_once()
        remove_from_task_state_mock.assert_called_once_with(job_from_task)

        assert len(caplog.records) == 1
        assert caplog.records[0].getMessage().startswith("Error in job executor. Task:")
