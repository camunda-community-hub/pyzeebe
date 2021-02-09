from random import randint
from unittest.mock import MagicMock
from uuid import uuid4

import grpc
import pytest
from zeebe_grpc.gateway_pb2 import *

from pyzeebe.exceptions import ActivateJobsRequestInvalid, JobAlreadyDeactivated, JobNotFound
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from tests.unit.utils.grpc_utils import GRPCStatusCode
from tests.unit.utils.random_utils import RANDOM_RANGE, random_job


def create_random_task_and_activate(grpc_servicer, task_type: str = None) -> str:
    if task_type:
        mock_task_type = task_type
    else:
        mock_task_type = str(uuid4())
    task = Task(task_type=mock_task_type, task_handler=lambda x: x, exception_handler=lambda x: x)
    job = random_job(task)
    grpc_servicer.active_jobs[job.key] = job
    return mock_task_type


def get_first_active_job(task_type, zeebe_adapter) -> Job:
    return next(zeebe_adapter.activate_jobs(task_type=task_type, max_jobs_to_activate=1, request_timeout=10,
                                            timeout=100, variables_to_fetch=[], worker=str(uuid4())))


def test_activate_jobs(zeebe_adapter, grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    active_jobs_count = randint(4, 100)
    counter = 0
    for i in range(0, active_jobs_count):
        create_random_task_and_activate(grpc_servicer, task_type)

    for job in zeebe_adapter.activate_jobs(task_type=task_type, worker=str(uuid4()), timeout=randint(10, 100),
                                           request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]):
        counter += 1
        assert isinstance(job, Job)
    assert counter == active_jobs_count + 1


def test_activate_jobs_invalid_worker(zeebe_adapter):
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=str(uuid4()), worker=None, timeout=randint(10, 100),
                                         request_timeout=100,
                                         max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_job_timeout(zeebe_adapter):
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=0,
                                         request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_task_type(zeebe_adapter):
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=None, worker=str(uuid4()), timeout=randint(10, 100),
                                         request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_max_jobs(zeebe_adapter):
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=randint(10, 100),
                                         request_timeout=100, max_jobs_to_activate=0, variables_to_fetch=[]))


def test_activate_jobs_common_errors_called(zeebe_adapter):
    zeebe_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_adapter._gateway_stub.ActivateJobs = MagicMock(side_effect=error)
    jobs = zeebe_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=randint(10, 100),
                                       request_timeout=100, max_jobs_to_activate=0, variables_to_fetch=[])
    for job in jobs:
        raise Exception(f"This should not return jobs! Job: {job}")

    zeebe_adapter._common_zeebe_grpc_errors.assert_called()


def test_complete_job(zeebe_adapter, grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    response = zeebe_adapter.complete_job(job_key=job.key, variables={})
    assert isinstance(response, CompleteJobResponse)


def test_complete_job_not_found(zeebe_adapter):
    with pytest.raises(JobNotFound):
        zeebe_adapter.complete_job(job_key=randint(0, RANDOM_RANGE), variables={})


def test_complete_job_already_completed(zeebe_adapter, grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    zeebe_adapter.complete_job(job_key=job.key, variables={})
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_adapter.complete_job(job_key=job.key, variables={})


def test_complete_job_common_errors_called(zeebe_adapter, grpc_servicer):
    zeebe_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_adapter._gateway_stub.CompleteJob = MagicMock(side_effect=error)

    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    zeebe_adapter.complete_job(job_key=job.key, variables={})

    zeebe_adapter._common_zeebe_grpc_errors.assert_called()


def test_fail_job(zeebe_adapter, grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    response = zeebe_adapter.fail_job(job_key=job.key, message=str(uuid4()))
    assert isinstance(response, FailJobResponse)


def test_fail_job_not_found(zeebe_adapter):
    with pytest.raises(JobNotFound):
        zeebe_adapter.fail_job(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))


def test_fail_job_already_failed(zeebe_adapter, grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    zeebe_adapter.fail_job(job_key=job.key, message=str(uuid4()))
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_adapter.fail_job(job_key=job.key, message=str(uuid4()))


def test_fail_job_common_errors_called(zeebe_adapter, grpc_servicer):
    zeebe_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_adapter._gateway_stub.FailJob = MagicMock(side_effect=error)

    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    zeebe_adapter.fail_job(job_key=job.key, message=str(uuid4()))

    zeebe_adapter._common_zeebe_grpc_errors.assert_called()


def test_throw_error(zeebe_adapter, grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    response = zeebe_adapter.throw_error(job_key=job.key, message=str(uuid4()))
    assert isinstance(response, ThrowErrorResponse)


def test_throw_error_job_not_found(zeebe_adapter):
    with pytest.raises(JobNotFound):
        zeebe_adapter.throw_error(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))


def test_throw_error_already_thrown(zeebe_adapter, grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    zeebe_adapter.throw_error(job_key=job.key, message=str(uuid4()))
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_adapter.throw_error(job_key=job.key, message=str(uuid4()))


def test_throw_error_common_errors_called(zeebe_adapter, grpc_servicer):
    zeebe_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_adapter._gateway_stub.ThrowError = MagicMock(side_effect=error)

    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type, zeebe_adapter)
    zeebe_adapter.throw_error(job_key=job.key, message=str(uuid4()))

    zeebe_adapter._common_zeebe_grpc_errors.assert_called()
