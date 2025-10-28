import asyncio
import json
from unittest.mock import AsyncMock, Mock

import pytest

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job, JobController
from pyzeebe.task.task import Task
from pyzeebe.worker.job_executor import JobExecutor, create_job_callback
from pyzeebe.worker.task_state import TaskState


@pytest.fixture
async def job_executor(task: Task, queue: asyncio.Queue, task_state: TaskState, zeebe_adapter: ZeebeAdapter):
    return JobExecutor(task, queue, task_state, zeebe_adapter)


@pytest.fixture(autouse=True)
def mock_job_handler(task: Task):
    task.job_handler = AsyncMock()


@pytest.mark.anyio
class TestExecuteOneJob:
    async def test_executes_jobs(
        self, job_executor: JobExecutor, job_from_task: Job, task: Task, job_controller: JobController
    ):
        await job_executor.execute_one_job(job_from_task, job_controller)

        task.job_handler.assert_called_with(job_from_task, job_controller)

    async def test_continues_on_deactivated_job(
        self, job_executor: JobExecutor, job_from_task: Job, job_controller: JobController
    ):
        await job_executor.execute_one_job(job_from_task, job_controller)
        await job_executor.execute_one_job(job_from_task, job_controller)


@pytest.mark.anyio
class TestGetNextJob:
    async def test_returns_expected_job(self, job_executor: JobExecutor, job_from_task: Job):
        await job_executor.jobs.put(job_from_task)

        assert await job_executor.get_next_job() == job_from_task


@pytest.mark.anyio
class TestShouldExecute:
    async def test_returns_true_on_default(self, job_executor: JobExecutor):
        assert job_executor.should_execute()

    async def test_returns_false_when_executor_is_stopped(self, job_executor: JobExecutor):
        await job_executor.stop()

        assert not job_executor.should_execute()


@pytest.mark.anyio
class TestStop:
    async def test_stops_executor(self, job_executor: JobExecutor):
        await job_executor.stop()

        await job_executor.execute()  # Implicitly test that execute returns immediately


@pytest.mark.anyio
class TestCreateJobCallback:
    async def test_returns_callable(self, job_executor: JobExecutor, job_from_task: Job):
        callback = create_job_callback(job_executor, job_from_task)

        assert callable(callback)

    async def test_signals_that_job_is_done(self, job_executor: JobExecutor, job_from_task: Job):
        task_done_mock = Mock()
        remove_from_task_state_mock = Mock()
        job_executor.jobs.task_done = task_done_mock
        job_executor.task_state.remove = remove_from_task_state_mock

        callback = create_job_callback(job_executor, job_from_task)
        callback(asyncio.Future())

        task_done_mock.assert_called_once()
        remove_from_task_state_mock.assert_called_once_with(job_from_task)

    async def test_signals_that_job_is_done_with_exception(
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
