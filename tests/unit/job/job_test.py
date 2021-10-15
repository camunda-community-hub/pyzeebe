from uuid import uuid4

import pytest
from mock import AsyncMock

from pyzeebe import Job
from pyzeebe.errors import NoZeebeAdapterError


@pytest.mark.asyncio
async def test_success(job_with_adapter):
    complete_job_mock = AsyncMock()
    job_with_adapter.zeebe_adapter.complete_job = complete_job_mock

    await job_with_adapter.set_success_status()

    complete_job_mock.assert_called_with(
        job_key=job_with_adapter.key, variables=job_with_adapter.variables
    )


@pytest.mark.asyncio
async def test_success_no_zeebe_adapter(job_without_adapter):
    with pytest.raises(NoZeebeAdapterError):
        await job_without_adapter.set_success_status()


@pytest.mark.asyncio
async def test_error(job_with_adapter):
    throw_error_mock = AsyncMock()
    job_with_adapter.zeebe_adapter.throw_error = throw_error_mock
    message = str(uuid4())

    await job_with_adapter.set_error_status(message)

    throw_error_mock.assert_called_with(
        job_key=job_with_adapter.key, message=message, error_code=""
    )


@pytest.mark.asyncio
async def test_error_with_code(job_with_adapter):
    throw_error_mock = AsyncMock()
    job_with_adapter.zeebe_adapter.throw_error = throw_error_mock
    message = str(uuid4())
    error_code = "custom-error-code"

    await job_with_adapter.set_error_status(message, error_code)

    throw_error_mock.assert_called_with(
        job_key=job_with_adapter.key, message=message, error_code=error_code
    )


@pytest.mark.asyncio
async def test_error_no_zeebe_adapter(job_without_adapter):
    with pytest.raises(NoZeebeAdapterError):
        message = str(uuid4())
        await job_without_adapter.set_error_status(message)


@pytest.mark.asyncio
async def test_failure(job_with_adapter):
    fail_job_mock = AsyncMock()
    job_with_adapter.zeebe_adapter.fail_job = fail_job_mock
    message = str(uuid4())

    await job_with_adapter.set_failure_status(message)

    fail_job_mock.assert_called_with(
        job_key=job_with_adapter.key, retries=job_with_adapter.retries-1, message=message
    )


@pytest.mark.asyncio
async def test_failure_no_zeebe_adapter(job_without_adapter):
    with pytest.raises(NoZeebeAdapterError):
        message = str(uuid4())
        await job_without_adapter.set_failure_status(message)


def test_equality_raises_not_implemented_on_other_type(job_without_adapter: Job):
    with pytest.raises(NotImplementedError):
        job_without_adapter == "test"
