from random import randint
from unittest.mock import MagicMock
from uuid import uuid4

from pyzeebe.client.client import ZeebeClient
from pyzeebe.exceptions import WorkflowNotFound
from tests.unit.utils.grpc_utils import *

zeebe_client: ZeebeClient


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


def test_deploy_workflow():
    zeebe_client.zeebe_adapter.deploy_workflow = MagicMock()
    file_path = str(uuid4())
    zeebe_client.deploy_workflow(file_path)
    zeebe_client.zeebe_adapter.deploy_workflow.assert_called_with(file_path)


def test_run_non_existent_workflow():
    with pytest.raises(WorkflowNotFound):
        zeebe_client.run_workflow(bpmn_process_id=str(uuid4()))


def test_run_non_existent_workflow_with_result():
    with pytest.raises(WorkflowNotFound):
        zeebe_client.run_workflow_with_result(bpmn_process_id=str(uuid4()))


def test_cancel_workflow_instance(grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_workflow(bpmn_process_id, version, [])
    workflow_instance_key = zeebe_client.run_workflow(bpmn_process_id=bpmn_process_id, variables={}, version=version)
    assert isinstance(zeebe_client.cancel_workflow_instance(workflow_instance_key=workflow_instance_key), int)


def test_publish_message():
    zeebe_client.publish_message(name=str(uuid4()), correlation_key=str(uuid4()))
