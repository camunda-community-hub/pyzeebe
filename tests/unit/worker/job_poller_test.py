import asyncio
import re

import pytest

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.job_poller import JobPoller
from pyzeebe.worker.task_state import TaskState
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.random_utils import random_job


@pytest.fixture
def job_poller(zeebe_adapter: ZeebeAdapter, task: Task, queue: asyncio.Queue, task_state: TaskState) -> JobPoller:
    return JobPoller(zeebe_adapter, task, queue, "test_worker", 100, task_state, 0)


@pytest.mark.asyncio
class TestPollOnce:
    async def test_one_job_is_polled(self, job_poller: JobPoller, queue: asyncio.Queue, job_from_task: Job,
                                     grpc_servicer: GatewayMock):
        grpc_servicer.active_jobs[job_from_task.key] = job_from_task

        await job_poller.poll_once()

        job: Job = queue.get_nowait()
        assert job.key == job_from_task.key

    async def test_no_job_is_polled(self, job_poller: JobPoller, queue: asyncio.Queue):
        await job_poller.poll_once()

        assert queue.empty()

    async def test_job_is_added_to_task_state(self, job_poller: JobPoller, job_from_task: Job, grpc_servicer: GatewayMock):
        grpc_servicer.active_jobs[job_from_task.key] = job_from_task

        await job_poller.poll_once()

        assert job_poller.task_state.count_active() == 1


class TestShouldPoll:
    def test_should_poll_returns_expected_result_when_disconnected(self, job_poller: JobPoller):
        job_poller.zeebe_adapter.connected = False
        job_poller.zeebe_adapter.retrying_connection = False

        assert not job_poller.should_poll()

    def test_continues_polling_when_retrying_connection(self, job_poller: JobPoller):
        job_poller.zeebe_adapter.connected = False
        job_poller.zeebe_adapter.retrying_connection = True

        assert job_poller.should_poll()

    @pytest.mark.asyncio
    async def test_stops_polling_after_poller_is_stopped(self, job_poller: JobPoller):
        await job_poller.stop()

        assert not job_poller.should_poll()


class TestMaxJobsToActivate:
    def test_returns_smallest_option(self, job_poller: JobPoller):
        job_poller.task.config.max_running_jobs = 0

        max_jobs_to_activate = job_poller.calculate_max_jobs_to_activate()

        assert max_jobs_to_activate == 0

    def test_returns_zero_when_max_number_of_jobs_are_running(self, job_poller: JobPoller):
        for _ in range(job_poller.task.config.max_running_jobs):
            job = random_job()
            job_poller.task_state.add(job)

        max_jobs_to_activate = job_poller.calculate_max_jobs_to_activate()

        assert max_jobs_to_activate == 0

    calculate_max_jobs_to_activate_cases = dict(
        max_running_jobs_minus_active_decides=(4, 10, 12, 6),
        max_running_jobs_minus_active_decides_2=(4, 12, 10, 8),
        max_running_jobs_minus_active_decides_zero_free=(4, 4, 12, 0),
        max_jobs_to_activate_decides=(4, 10, 5, 5),
        max_jobs_to_activate_decides_zero_active=(0, 10, 5, 5)
    )

    @pytest.mark.parametrize("active_jobs,max_running_jobs,max_jobs_to_activate_on_task,expected",
                             calculate_max_jobs_to_activate_cases.values(),
                             ids=calculate_max_jobs_to_activate_cases.keys())
    def test_calculate_max_jobs_to_activate(self, job_poller: JobPoller, active_jobs: int, max_running_jobs: int,
                                            max_jobs_to_activate_on_task: int, expected: int):
        job_poller.task.config.max_running_jobs = max_running_jobs
        job_poller.task.config.max_jobs_to_activate = max_jobs_to_activate_on_task

        for _ in range(active_jobs):
            job = random_job()
            job_poller.task_state.add(job)

        max_jobs_to_activate = job_poller.calculate_max_jobs_to_activate()

        assert max_jobs_to_activate == expected


@pytest.mark.asyncio
class TestActivateMaxJobs:
    async def test_writes_warning_log_when_no_jobs_to_activate(self, job_poller: JobPoller, caplog):
        job_poller.poll_retry_delay = 0
        job_poller.task.config.max_running_jobs = 0

        await job_poller.activate_max_jobs()

        assert re.search("Maximum number of jobs running for .*. Polling again in 0 seconds...", caplog.text)

    async def test_puts_job_in_queue_with_one_available_job(self, job_poller: JobPoller, queue: asyncio.Queue, job_from_task: Job,
                                     grpc_servicer: GatewayMock):
        grpc_servicer.active_jobs[job_from_task.key] = job_from_task

        await job_poller.activate_max_jobs()

        job: Job = queue.get_nowait()
        assert job.key == job_from_task.key
