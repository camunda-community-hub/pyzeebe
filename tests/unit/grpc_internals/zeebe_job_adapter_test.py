from random import randint
from uuid import uuid4

import pytest
from zeebe_grpc.gateway_pb2 import (CompleteJobResponse, FailJobResponse,
                                    ThrowErrorResponse)

from pyzeebe.errors import (ActivateJobsRequestInvalidError,
                            JobAlreadyDeactivatedError, JobNotFoundError)
from pyzeebe.grpc_internals.zeebe_job_adapter import ZeebeJobAdapter
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.random_utils import RANDOM_RANGE, random_job


def random_job_key() -> int:
    return randint(0, RANDOM_RANGE)


def random_message() -> str:
    return str(uuid4())


@pytest.mark.asyncio
class TestActivateJobs:
    zeebe_job_adapter: ZeebeJobAdapter

    @pytest.fixture(autouse=True)
    def set_up(self, zeebe_adapter: ZeebeJobAdapter):
        self.zeebe_job_adapter = zeebe_adapter

    def activate_jobs(
        self,
        task_type=str(uuid4()),
        worker=str(uuid4()),
        timeout=randint(10, 100),
        request_timeout=100,
        max_jobs_to_activate=1,
        variables_to_fetch=[]
    ):
        return self.zeebe_job_adapter.activate_jobs(task_type, worker, timeout, max_jobs_to_activate, variables_to_fetch, request_timeout)

    async def test_returns_correct_amount_of_jobs(self, grpc_servicer: GatewayMock, task: Task):
        active_jobs_count = randint(4, 100)
        for _ in range(0, active_jobs_count):
            job = random_job(task)
            grpc_servicer.active_jobs[job.key] = job

        jobs = self.activate_jobs(task_type=task.type)

        assert len([job async for job in jobs]) == active_jobs_count

    async def test_raises_on_invalid_worker(self):
        with pytest.raises(ActivateJobsRequestInvalidError):
            jobs = self.activate_jobs(worker=None)
            await jobs.__anext__()

    async def test_raises_on_invalid_job_timeout(self):
        with pytest.raises(ActivateJobsRequestInvalidError):
            jobs = self.activate_jobs(timeout=0)
            await jobs.__anext__()

    async def test_raises_on_invalid_task_type(self):
        with pytest.raises(ActivateJobsRequestInvalidError):
            jobs = self.activate_jobs(task_type=None)
            await jobs.__anext__()

    async def test_raises_on_invalid_max_jobs(self):
        with pytest.raises(ActivateJobsRequestInvalidError):
            jobs = self.activate_jobs(max_jobs_to_activate=0)
            await jobs.__anext__()


@pytest.mark.asyncio
class TestCompleteJob:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeJobAdapter, first_active_job: Job):
        response = await zeebe_adapter.complete_job(first_active_job.key, {})

        assert isinstance(response, CompleteJobResponse)

    async def test_raises_on_fake_job(self, zeebe_adapter: ZeebeJobAdapter):
        with pytest.raises(JobNotFoundError):
            await zeebe_adapter.complete_job(random_job_key(), {})

    async def test_raises_on_already_completed_job(self, zeebe_adapter: ZeebeJobAdapter, first_active_job: Job):
        await zeebe_adapter.complete_job(first_active_job.key, {})

        with pytest.raises(JobAlreadyDeactivatedError):
            await zeebe_adapter.complete_job(first_active_job.key, {})


@pytest.mark.asyncio
class TestFailJob:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeJobAdapter, first_active_job: Job):
        response = await zeebe_adapter.fail_job(first_active_job.key, first_active_job.retries, random_message())

        assert isinstance(response, FailJobResponse)

    async def test_raises_on_fake_job(self, zeebe_adapter: ZeebeJobAdapter):
        with pytest.raises(JobNotFoundError):
            await zeebe_adapter.fail_job(random_job_key(), 1, random_message())

    async def test_raises_on_deactivated_job(self, zeebe_adapter: ZeebeJobAdapter, first_active_job: Job):
        await zeebe_adapter.fail_job(first_active_job.key, first_active_job.retries, random_message())

        with pytest.raises(JobAlreadyDeactivatedError):
            await zeebe_adapter.fail_job(first_active_job.key, first_active_job.retries, random_message())


@pytest.mark.asyncio
class TestThrowError:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeJobAdapter, first_active_job: Job):
        response = await zeebe_adapter.throw_error(first_active_job.key, random_message())

        assert isinstance(response, ThrowErrorResponse)

    async def test_raises_on_fake_job(self, zeebe_adapter: ZeebeJobAdapter):
        with pytest.raises(JobNotFoundError):
            await zeebe_adapter.throw_error(random_job_key(), random_message())

    async def test_raises_on_deactivated_job(self, zeebe_adapter: ZeebeJobAdapter, first_active_job: Job):
        await zeebe_adapter.throw_error(first_active_job.key, random_message())

        with pytest.raises(JobAlreadyDeactivatedError):
            await zeebe_adapter.throw_error(first_active_job.key, random_message())
