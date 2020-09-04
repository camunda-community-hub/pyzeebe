from io import BytesIO
from random import randint
from unittest.mock import patch
from uuid import uuid4

import grpc
import pytest

from pyzeebe.common.exceptions import *
from pyzeebe.common.gateway_mock import GatewayMock
from pyzeebe.common.random_utils import RANDOM_RANGE, random_task_context
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.grpc_internals.zeebe_pb2 import *
from pyzeebe.task.task import Task
from pyzeebe.task.task_context import TaskContext

zeebe_adapter: ZeebeAdapter


@pytest.fixture(scope='module')
def grpc_add_to_server():
    from pyzeebe.grpc_internals.zeebe_pb2_grpc import add_GatewayServicer_to_server
    return add_GatewayServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
    return GatewayMock()


@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
    from pyzeebe.grpc_internals.zeebe_pb2_grpc import GatewayStub
    return GatewayStub


@pytest.fixture(autouse=True)
def run_around_tests(grpc_channel):
    global zeebe_adapter
    zeebe_adapter = ZeebeAdapter(channel=grpc_channel)
    yield
    zeebe_adapter = ZeebeAdapter(channel=grpc_channel)


def test_connectivity_ready():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.READY)
    assert not zeebe_adapter.retrying_connection
    assert zeebe_adapter.connected


def test_connectivity_transient_idle():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.IDLE)
    assert not zeebe_adapter.retrying_connection
    assert zeebe_adapter.connected


def test_connectivity_connecting():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.CONNECTING)
    assert zeebe_adapter.retrying_connection
    assert not zeebe_adapter.connected


def test_connectivity_transient_failure():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.TRANSIENT_FAILURE)
    assert zeebe_adapter.retrying_connection
    assert not zeebe_adapter.connected


def test_connectivity_shutdown():
    with pytest.raises(ConnectionAbortedError):
        zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.SHUTDOWN)


def test_only_port():
    port = randint(0, 10000)
    zeebe_adapter = ZeebeAdapter(port=port)
    assert zeebe_adapter.connection_uri == f'localhost:{port}'


def test_only_host():
    hostname = str(uuid4())
    zeebe_adapter = ZeebeAdapter(hostname=hostname)
    assert zeebe_adapter.connection_uri == f'{hostname}:26500'


def test_host_and_port():
    hostname = str(uuid4())
    port = randint(0, 10000)
    zeebe_adapter = ZeebeAdapter(hostname=hostname, port=port)
    assert zeebe_adapter.connection_uri == f'{hostname}:{port}'


def test_activate_jobs(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    active_jobs_count = randint(4, 100)
    counter = 0
    for i in range(0, active_jobs_count):
        create_random_task_and_activate(grpc_servicer, task_type)

    for job in zeebe_adapter.activate_jobs(task_type=task_type, worker=str(uuid4()), timeout=randint(10, 100),
                                           request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]):
        counter += 1
        assert isinstance(job, TaskContext)
    assert counter == active_jobs_count + 1


def test_activate_jobs_invalid_worker():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=str(uuid4()), worker=None, timeout=randint(10, 100),
                                         request_timeout=100,
                                         max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_job_timeout():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=0,
                                         request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_task_type():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=None, worker=str(uuid4()), timeout=randint(10, 100),
                                         request_timeout=100, max_jobs_to_activate=1, variables_to_fetch=[]))


def test_activate_jobs_invalid_max_jobs():
    with pytest.raises(ActivateJobsRequestInvalid):
        next(zeebe_adapter.activate_jobs(task_type=str(uuid4()), worker=str(uuid4()), timeout=randint(10, 100),
                                         request_timeout=100, max_jobs_to_activate=0, variables_to_fetch=[]))


def test_complete_job(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    response = zeebe_adapter.complete_job(job_key=job.key, variables={})
    assert isinstance(response, CompleteJobResponse)


def test_complete_job_not_found(grpc_servicer):
    with pytest.raises(JobNotFound):
        zeebe_adapter.complete_job(job_key=randint(0, RANDOM_RANGE), variables={})


def test_complete_job_already_completed(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_adapter.complete_job(job_key=job.key, variables={})
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_adapter.complete_job(job_key=job.key, variables={})


def test_fail_job(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    response = zeebe_adapter.fail_job(job_key=job.key, message=str(uuid4()))
    assert isinstance(response, FailJobResponse)


def test_fail_job_not_found():
    with pytest.raises(JobNotFound):
        zeebe_adapter.fail_job(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))


def test_fail_job_already_failed(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_adapter.fail_job(job_key=job.key, message=str(uuid4()))
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_adapter.fail_job(job_key=job.key, message=str(uuid4()))


def test_throw_error(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    response = zeebe_adapter.throw_error(job_key=job.key, message=str(uuid4()))
    assert isinstance(response, ThrowErrorResponse)


def test_throw_error_job_not_found():
    with pytest.raises(JobNotFound):
        zeebe_adapter.throw_error(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))


def test_throw_error_already_thrown(grpc_servicer):
    task_type = create_random_task_and_activate(grpc_servicer)
    job = get_first_active_job(task_type)
    zeebe_adapter.throw_error(job_key=job.key, message=str(uuid4()))
    with pytest.raises(JobAlreadyDeactivated):
        zeebe_adapter.throw_error(job_key=job.key, message=str(uuid4()))


def test_create_workflow_instance(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    response = zeebe_adapter.create_workflow_instance(bpmn_process_id=bpmn_process_id, variables={}, version=version)
    assert isinstance(response, int)


def test_create_workflow_instance_with_result(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    response = zeebe_adapter.create_workflow_instance_with_result(bpmn_process_id=bpmn_process_id, variables={},
                                                                  version=version, timeout=0, variables_to_fetch=[])
    assert isinstance(response, dict)


def test_publish_message():
    response = zeebe_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                             time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))
    assert isinstance(response, PublishMessageResponse)


def create_random_task_and_activate(grpc_servicer, task_type: str = None) -> str:
    if task_type:
        mock_task_type = task_type
    else:
        mock_task_type = str(uuid4())
    task = Task(task_type=mock_task_type, task_handler=lambda x: x, exception_handler=lambda x: x)
    task_context = random_task_context(task)
    grpc_servicer.active_jobs[task_context.key] = task_context
    return mock_task_type


def get_first_active_job(task_type) -> TaskContext:
    return next(zeebe_adapter.activate_jobs(task_type=task_type, max_jobs_to_activate=1, request_timeout=10,
                                            timeout=100, variables_to_fetch=[], worker=str(uuid4())))


def test_get_workflow_request_object():
    with patch('builtins.open') as mock_open:
        mock_open.return_value = BytesIO()
        file_path = str(uuid4())
        zeebe_adapter._get_workflow_request_object(file_path)
        mock_open.assert_called_with(file_path, 'rb')
