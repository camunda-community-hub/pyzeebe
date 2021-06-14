import asyncio

import pytest
from mock import AsyncMock, Mock

from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.job_executor import JobExecutor, create_job_callback
from pyzeebe.worker.task_state import TaskState


@pytest.fixture
def job_executor(task: Task, queue: asyncio.Queue, task_state: TaskState):
    return JobExecutor(task, queue, task_state)


@pytest.fixture(autouse=True)
def mock_job_handler(task: Task):
    task.job_handler = AsyncMock()


@pytest.mark.asyncio
class TestExecuteOneJob:
    async def test_executes_jobs(self, job_executor: JobExecutor, job_from_task: Job, task: Task):
        await job_executor.execute_one_job(job_from_task)

        task.job_handler.assert_called_with(job_from_task)

    async def test_continues_on_deactivated_job(self, job_executor: JobExecutor, job_from_task: Job):
        await job_executor.execute_one_job(job_from_task)
        await job_executor.execute_one_job(job_from_task)


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
