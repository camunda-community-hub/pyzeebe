from io import BytesIO
from random import randint
from unittest.mock import patch
from uuid import uuid4

import grpc
import pytest

from pyzeebe.common.gateway_mock import GatewayMock
from pyzeebe.common.random_utils import RANDOM_RANGE
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.grpc_internals.zeebe_pb2 import *

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


def test_complete_job():
    response = zeebe_adapter.complete_job(job_key=randint(0, RANDOM_RANGE), variables={})
    assert isinstance(response, CompleteJobResponse)


def test_fail_job():
    response = zeebe_adapter.fail_job(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))
    assert isinstance(response, FailJobResponse)


def test_throw_error():
    response = zeebe_adapter.throw_error(job_key=randint(0, RANDOM_RANGE), message=str(uuid4()))
    assert isinstance(response, ThrowErrorResponse)


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


def test_get_workflow_request_object():
    with patch('builtins.open') as mock_open:
        mock_open.return_value = BytesIO()
        file_path = str(uuid4())
        zeebe_adapter._get_workflow_request_object(file_path)
        mock_open.assert_called_with(file_path, 'rb')
