from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.exceptions import NoZeebeAdapter
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from tests.unit.utils.random_utils import random_job

job: Job


@pytest.fixture(autouse=True)
def run_around_tests():
    zeebe_adapter = ZeebeAdapter()
    global job
    job = random_job(zeebe_adapter=zeebe_adapter)
    yield
    job = random_job(zeebe_adapter=zeebe_adapter)


def test_success():
    with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as complete_job_mock:
        job.set_success_status()
        complete_job_mock.assert_called_with(job_key=job.key, variables=job.variables)


def test_success_no_zeebe_adapter():
    global job
    job = random_job()

    with pytest.raises(NoZeebeAdapter):
        job.set_success_status()


def test_error():
    with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.throw_error") as throw_error_mock:
        message = str(uuid4())
        job.set_error_status(message)
        throw_error_mock.assert_called_with(job_key=job.key, message=message)


def test_error_no_zeebe_adapter():
    global job
    job = random_job()

    with pytest.raises(NoZeebeAdapter):
        message = str(uuid4())
        job.set_error_status(message)


def test_failure():
    with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.fail_job") as fail_job_mock:
        message = str(uuid4())
        job.set_failure_status(message)
        fail_job_mock.assert_called_with(job_key=job.key, message=message)


def test_failure_no_zeebe_adapter():
    global job
    job = random_job()

    with pytest.raises(NoZeebeAdapter):
        message = str(uuid4())
        job.set_failure_status(message)
