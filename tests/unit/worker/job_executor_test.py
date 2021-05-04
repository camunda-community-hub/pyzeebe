import asyncio
from unittest.mock import AsyncMock

import pytest

from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.job_executor import JobExecutor
from tests.unit.utils.random_utils import randint


@pytest.fixture
def job_executor(task: Task, queue: asyncio.Queue):
    return JobExecutor(task, queue)


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
