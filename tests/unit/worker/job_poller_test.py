import asyncio

import pytest

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.job_poller import JobPoller
from tests.unit.utils.gateway_mock import GatewayMock


@pytest.fixture
def queue():
    return asyncio.Queue()


@pytest.fixture
def job_poller(zeebe_adapter: ZeebeAdapter, task: Task, queue: asyncio.Queue) -> JobPoller:
    return JobPoller(zeebe_adapter, task, queue, "test_worker", 100)


@pytest.mark.asyncio
class TestPollOnce:
    async def test_one_job_is_polled(self, job_poller: JobPoller, queue: asyncio.Queue, job_from_task: Job, grpc_servicer: GatewayMock):
        grpc_servicer.active_jobs[job_from_task.key] = job_from_task

        await job_poller.poll_once()

        job: Job = await queue.get()
        assert job.key == job_from_task.key

    async def test_no_job_is_polled(self, job_poller: JobPoller, queue: asyncio.Queue, job_from_task: Job):
        await job_poller.poll_once()

        assert queue.empty()


class TestShouldPoll:
    def test_should_poll_returns_expected_result_when_disconnected(self, job_poller: JobPoller):
        job_poller.zeebe_adapter.connected = False
        job_poller.zeebe_adapter.retrying_connection = False

        assert not job_poller.should_poll()

    def test_continues_polling_when_retrying_connection(self, job_poller: JobPoller):
        job_poller.zeebe_adapter.connected = False
        job_poller.zeebe_adapter.retrying_connection = True

        assert job_poller.should_poll()

    def test_stops_polling_after_poller_is_stopped(self, job_poller: JobPoller):
        job_poller.stop()

        assert not job_poller.should_poll()
