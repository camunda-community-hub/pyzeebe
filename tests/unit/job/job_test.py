from uuid import uuid4

import pytest
from mock import AsyncMock

from pyzeebe import JobStatus
from pyzeebe.errors import NoZeebeAdapterError


@pytest.mark.asyncio
class TestSetSuccessStatus:
    async def test_updates_job_in_zeebe(self, job_with_adapter):
        complete_job_mock = AsyncMock()
        job_with_adapter.zeebe_adapter.complete_job = complete_job_mock

        await job_with_adapter.set_success_status()

        complete_job_mock.assert_called_with(job_key=job_with_adapter.key, variables=job_with_adapter.variables)

    async def test_status_is_set(self, job_with_adapter):
        complete_job_mock = AsyncMock()
        job_with_adapter.zeebe_adapter.complete_job = complete_job_mock

        await job_with_adapter.set_success_status()

        assert job_with_adapter.status == JobStatus.Completed

    async def test_raises_without_zeebe_adapter(self, job_without_adapter):
        with pytest.raises(NoZeebeAdapterError):
            await job_without_adapter.set_success_status()


@pytest.mark.asyncio
class TestSetErrorStatus:
    async def test_updates_job_in_zeebe(self, job_with_adapter):
        throw_error_mock = AsyncMock()
        job_with_adapter.zeebe_adapter.throw_error = throw_error_mock
        message = str(uuid4())

        await job_with_adapter.set_error_status(message)

        throw_error_mock.assert_called_with(job_key=job_with_adapter.key, message=message, error_code="")

    async def test_updates_job_in_zeebe_with_code(self, job_with_adapter):
        throw_error_mock = AsyncMock()
        job_with_adapter.zeebe_adapter.throw_error = throw_error_mock
        message = str(uuid4())
        error_code = "custom-error-code"

        await job_with_adapter.set_error_status(message, error_code)

        throw_error_mock.assert_called_with(job_key=job_with_adapter.key, message=message, error_code=error_code)

    async def test_status_is_set(self, job_with_adapter):
        throw_error_mock = AsyncMock()
        job_with_adapter.zeebe_adapter.throw_error = throw_error_mock
        message = str(uuid4())

        await job_with_adapter.set_error_status(message)

        assert job_with_adapter.status == JobStatus.ErrorThrown

    async def test_raises_without_zeebe_adapter(self, job_without_adapter):
        with pytest.raises(NoZeebeAdapterError):
            message = str(uuid4())
            await job_without_adapter.set_error_status(message)


@pytest.mark.asyncio
class TestSetFailureStatus:
    async def test_updates_job_in_zeebe(self, job_with_adapter):
        fail_job_mock = AsyncMock()
        job_with_adapter.zeebe_adapter.fail_job = fail_job_mock
        message = str(uuid4())

        await job_with_adapter.set_failure_status(message)

        fail_job_mock.assert_called_with(
            job_key=job_with_adapter.key, retries=job_with_adapter.retries - 1, message=message, retry_backoff=None
        )

    async def test_status_is_set(self, job_with_adapter):
        fail_job_mock = AsyncMock()
        job_with_adapter.zeebe_adapter.fail_job = fail_job_mock
        message = str(uuid4())

        await job_with_adapter.set_failure_status(message)

        assert job_with_adapter.status == JobStatus.Failed

    async def test_raises_without_zeebe_adapter(self, job_without_adapter):
        with pytest.raises(NoZeebeAdapterError):
            message = str(uuid4())
            await job_without_adapter.set_failure_status(message)
