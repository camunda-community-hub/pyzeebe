from random import randint
from unittest.mock import patch
from uuid import uuid4

import grpc
import pytest

from pyzeebe.common.random_utils import RANDOM_RANGE
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.grpc_internals.zeebe_pb2 import *
from pyzeebe.grpc_internals.zeebe_pb2_grpc import GatewayServicer

zeebe_adapter: ZeebeAdapter


@patch('grpc.insecure_channel')
def mock_channel():
    pass


class TestGatewayServicer(GatewayServicer):
    """
    def ActivateJobs(self, request, context):
        return ActivateJobsResponse(jobs=[ActivatedJob()])
    """

    def __init__(self):
        self.workflows = {}

    def CompleteJob(self, request, context):
        return CompleteJobResponse()

    def FailJob(self, request, context):
        return FailJobResponse()

    def ThrowError(self, request, context):
        return ThrowErrorResponse()

    def CreateWorkflowInstance(self, request, context):
        return CreateWorkflowInstanceResponse(workflowKey=randint(0, RANDOM_RANGE),
                                              bpmnProcessId=request.bpmnProcessId,
                                              version=request.version, workflowInstanceKey=randint(0, RANDOM_RANGE))

    def CreateWorkflowInstanceWithResult(self, request, context):
        return CreateWorkflowInstanceWithResultResponse(workflowKey=request.request.workflowKey,
                                                        bpmnProcessId=request.request.bpmnProcessId,
                                                        version=randint(0, 10), variables=request.request.variables)

    def DeployWorkflow(self, request, context):
        workflows = []
        for workflow in request.workflows:
            workflow_metadata = WorkflowMetadata(bpmnProcessId=str(uuid4()), version=randint(0, 10),
                                                 workflowKey=randint(0, RANDOM_RANGE), resourceName=workflow.name)
            workflows.append(workflow_metadata)
            self.workflows[workflow_metadata.bpmnProcessId] = workflow_metadata

        return DeployWorkflowResponse(key=randint(0, RANDOM_RANGE), workflows=workflows)

    def PublishMessage(self, request, context):
        return PublishMessageResponse()


@pytest.fixture(scope='module')
def grpc_add_to_server():
    from pyzeebe.grpc_internals.zeebe_pb2_grpc import add_GatewayServicer_to_server
    return add_GatewayServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
    return TestGatewayServicer()


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


def test_create_workflow_instance():
    response = zeebe_adapter.create_workflow_instance(bpmn_process_id=str(uuid4()), variables={},
                                                      version=randint(0, 10))
    assert isinstance(response, int)


def test_create_workflow_instance_with_result():
    response = zeebe_adapter.create_workflow_instance_with_result(bpmn_process_id=str(uuid4()), variables={},
                                                                  version=randint(0, 10), timeout=0,
                                                                  variables_to_fetch=[])
    assert isinstance(response, dict)


def test_publish_message():
    response = zeebe_adapter.publish_message(name=str(uuid4()), variables={}, correlation_key=str(uuid4()),
                                             time_to_live_in_milliseconds=randint(0, RANDOM_RANGE))
    assert isinstance(response, PublishMessageResponse)
