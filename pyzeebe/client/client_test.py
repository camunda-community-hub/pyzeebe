from random import randint
from uuid import uuid4

import pytest

from pyzeebe.client.client import ZeebeClient
from pyzeebe.common.exceptions import WorkflowNotFound
from pyzeebe.common.gateway_mock import GatewayMock
from pyzeebe.common.random_utils import RANDOM_RANGE

zeebe_client: ZeebeClient


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
    global zeebe_client
    zeebe_client = ZeebeClient(channel=grpc_channel)
    yield
    zeebe_client = ZeebeClient(channel=grpc_channel)


def test_run_workflow(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    assert isinstance(zeebe_client.run_workflow(bpmn_process_id=bpmn_process_id, variables={}, version=version), int)


def test_run_workflow_with_result(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    assert isinstance(zeebe_client.run_workflow(bpmn_process_id=bpmn_process_id, variables={}, version=version), int)


def test_deploy_workflow(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    assert bpmn_process_id in grpc_servicer.deployed_workflows.keys()


def test_run_non_existent_workflow():
    with pytest.raises(WorkflowNotFound):
        zeebe_client.run_workflow(bpmn_process_id=str(uuid4()))


def test_run_non_existent_workflow_with_result():
    with pytest.raises(WorkflowNotFound):
        zeebe_client.run_workflow_with_result(bpmn_process_id=str(uuid4()))


def test_cancel_workflow_instance():
    assert isinstance(zeebe_client.cancel_workflow_instance(workflow_instance_key=randint(0, RANDOM_RANGE)), int)


def test_publish_message():
    zeebe_client.publish_message(name=str(uuid4()), correlation_key=str(uuid4()))
