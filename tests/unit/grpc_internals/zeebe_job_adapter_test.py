from random import randint
from unittest.mock import MagicMock
from uuid import uuid4

from zeebe_grpc.gateway_pb2 import *

from pyzeebe.exceptions import ActivateJobsRequestInvalid, JobAlreadyDeactivated, JobNotFound
from pyzeebe.grpc_internals.zeebe_job_adapter import ZeebeJobAdapter
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from tests.unit.utils.grpc_utils import *
from tests.unit.utils.random_utils import RANDOM_RANGE, random_job

zeebe_job_adapter: ZeebeJobAdapter


def create_random_task_and_activate(grpc_servicer, task_type: str = None) -> str:
    if task_type:
        mock_task_type = task_type
    else:
        mock_task_type = str(uuid4())
    task = Task(task_type=mock_task_type, task_handler=lambda x: x, exception_handler=lambda x: x)
    job = random_job(task)
    grpc_servicer.active_jobs[job.key] = job
    return mock_task_type


def get_first_active_job(task_type) -> Job:
    return next(zeebe_job_adapter.activate_jobs(task_type=task_type, max_jobs_to_activate=1, request_timeout=10,
                                                timeout=100, variables_to_fetch=[], worker=str(uuid4())))


@pytest.fixture(autouse=True)
def run_around_tests(grpc_channel):
    global zeebe_job_adapter
    zeebe_job_adapter = ZeebeJobAdapter(channel=grpc_channel)
    yield
    zeebe_job_adapter = ZeebeJobAdapter(channel=grpc_channel)


def test_activate_jobs(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    active_jobs_count = randint(4, 100)
    counter = 0
    for i in range(0, active_jobs_count):
        create_random_task_and_activate(grpc_servicer, task_type)

    for job in zeebe_job_adapter.activate_jobs(task_type=task_type, worker=str(uuid4()), timeout=randint(10, 100),
                                               request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]):
        counter += 1
        assert isinstance(job, Job)
    assert counter == active_jobs_count + 1


def test_activate_jobs_invalid_worker():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_job_adapter.activate_jobs(task_type=str(uuid4()), worker=None, timeout=randint(10, 100),
                                             request_timeout=100,
                                             max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_job_timeout():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_job_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=0,
                                             request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_task_type():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_job_adapter.activate_jobs(task_type=None, worker=str(uuid4()), timeout=randint(10, 100),
                                             request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_max_jobs():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_job_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=randint(10, 100),
                                             request_timeout=100, max_jobs_to_activate=0, variables_to_fetch=[]))


def test_activate_jobs_common_errors_called(grpc_servicer):
    zeebe_job_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_job_adapter._gateway_stub.ActivateJobs = MagicMock(side_effect=error)
    jobs = zeebe_job_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=randint(10, 100),
                                           request_timeout=100, max_jobs_to_activate=0, variables_to_fetch=[])
    for job in jobs:
        raise Exception(f"This should not return jobs! Job: {job}")

    zeebe_job_adapter._common_zeebe_grpc_errors.assert_called()


def test_throw_error_common_errors_called(grpc_servicer):
    zeebe_job_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_job_adapter._gateway_stub.ActivateJobs = MagicMock(side_effect=error)

    zeebe_job_adapter.zeebe_job_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()),
                                                      timeout=randint(10, 100),
                                                      request_timeout=100, max_jobs_to_activate=0,
                                                      variables_to_fetch=[])

    zeebe_job_adapter._common_zeebe_grpc_errors.assert_called()


def test_complete_job(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    response = zeebe_job_adapter.complete_job(job_key=job.key, variables={})
    assert isinstance(response, CompleteJobResponse)


def test_complete_job_not_found(grpc_servicer):
    with pytest.raises(JobNotFound):
        zeebe_job_adapter.complete_job(job_key=randint(0, RANDOM_RANGE), variables={})


def test_complete_job_already_completed(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_job_adapter.complete_job(job_key=job.key, variables={})
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_job_adapter.complete_job(job_key=job.key, variables={})


def test_complete_job_common_errors_called(grpc_servicer):
    zeebe_job_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_job_adapter._gateway_stub.CompleteJob = MagicMock(side_effect=error)

    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_job_adapter.complete_job(job_key=job.key, variables={})

    zeebe_job_adapter._common_zeebe_grpc_errors.assert_called()


def test_fail_job(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    response = zeebe_job_adapter.fail_job(job_key=job.key, message=str(uuid4()))
    assert isinstance(response, FailJobResponse)


def test_fail_job_not_found():
    with pytest.raises(JobNotFound):
        zeebe_job_adapter.fail_job(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))


def test_fail_job_already_failed(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_job_adapter.fail_job(job_key=job.key, message=str(uuid4()))
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_job_adapter.fail_job(job_key=job.key, message=str(uuid4()))


def test_fail_job_common_errors_called(grpc_servicer):
    zeebe_job_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_job_adapter._gateway_stub.FailJob = MagicMock(side_effect=error)

    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_job_adapter.fail_job(job_key=job.key, message=str(uuid4()))

    zeebe_job_adapter._common_zeebe_grpc_errors.assert_called()


def test_throw_error(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    response = zeebe_job_adapter.throw_error(job_key=job.key, message=str(uuid4()))
    assert isinstance(response, ThrowErrorResponse)


def test_throw_error_job_not_found():
    with pytest.raises(JobNotFound):
        zeebe_job_adapter.throw_error(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))


def test_throw_error_already_thrown(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_job_adapter.throw_error(job_key=job.key, message=str(uuid4()))
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_job_adapter.throw_error(job_key=job.key, message=str(uuid4()))


def test_throw_error_common_errors_called(grpc_servicer):
    zeebe_job_adapter._common_zeebe_grpc_errors = MagicMock()
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)

    zeebe_job_adapter._gateway_stub.ThrowError = MagicMock(side_effect=error)

    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_job_adapter.throw_error(job_key=job.key, message=str(uuid4()))

    zeebe_job_adapter._common_zeebe_grpc_errors.assert_called()
