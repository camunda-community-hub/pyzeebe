from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from pyzeebe import Job, JobController, JobStatus


@pytest.mark.anyio
class TestSetSuccessStatus:
    async def test_updates_job_in_zeebe(self, job: Job, job_controller: JobController):
        complete_job_mock = AsyncMock()
        job_controller._zeebe_adapter.complete_job = complete_job_mock

        await job_controller.set_success_status()

        complete_job_mock.assert_called_with(job_key=job.key, variables=job.variables)

    async def test_status_is_set(self, job: Job, job_controller: JobController):
        complete_job_mock = AsyncMock()
        job_controller._zeebe_adapter.complete_job = complete_job_mock

        await job_controller.set_success_status()

        assert job.status == JobStatus.Completed


@pytest.mark.anyio
class TestSetErrorStatus:
    async def test_updates_job_in_zeebe(self, job: Job, job_controller: JobController):
        throw_error_mock = AsyncMock()
        job_controller._zeebe_adapter.throw_error = throw_error_mock
        message = str(uuid4())

        await job_controller.set_error_status(message)

        throw_error_mock.assert_called_with(job_key=job.key, message=message, error_code="", variables={})

    async def test_updates_job_in_zeebe_with_code(self, job: Job, job_controller: JobController):
        throw_error_mock = AsyncMock()
        job_controller._zeebe_adapter.throw_error = throw_error_mock
        message = str(uuid4())
        error_code = "custom-error-code"

        await job_controller.set_error_status(message, error_code)

        throw_error_mock.assert_called_with(job_key=job.key, message=message, error_code=error_code, variables={})

    async def test_status_is_set(self, job: Job, job_controller: JobController):
        throw_error_mock = AsyncMock()
        job_controller._zeebe_adapter.throw_error = throw_error_mock
        message = str(uuid4())

        await job_controller.set_error_status(message)

        assert job.status == JobStatus.ErrorThrown


@pytest.mark.anyio
class TestSetFailureStatus:
    async def test_updates_job_in_zeebe(self, job: Job, job_controller: JobController):
        fail_job_mock = AsyncMock()
        job_controller._zeebe_adapter.fail_job = fail_job_mock
        message = str(uuid4())

        await job_controller.set_failure_status(message)

        fail_job_mock.assert_called_with(
            job_key=job.key,
            retries=job.retries - 1,
            message=message,
            retry_back_off_ms=0,
            variables={},
        )

    async def test_status_is_set(self, job: Job, job_controller: JobController):
        fail_job_mock = AsyncMock()
        job_controller._zeebe_adapter.fail_job = fail_job_mock
        message = str(uuid4())

        await job_controller.set_failure_status(message)

        assert job.status == JobStatus.Failed
