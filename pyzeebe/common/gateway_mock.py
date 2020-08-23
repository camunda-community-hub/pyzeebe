from random import randint
from typing import Dict
from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.common.random_utils import RANDOM_RANGE
from pyzeebe.grpc_internals.zeebe_pb2 import *
from pyzeebe.grpc_internals.zeebe_pb2_grpc import GatewayServicer


@patch('grpc.insecure_channel')
def mock_channel():
    pass


deployed_workflows: Dict


@pytest.fixture(autouse=True)
def run_around_tests(grpc_channel):
    global deployed_workflows
    deployed_workflows = {}
    yield
    deployed_workflows = {}


class GatewayMock(GatewayServicer):
    # TODO: Mock behaviour of zeebe

    def __init__(self):
        self.deployed_workflows = {}

    def CompleteJob(self, request, context):
        return CompleteJobResponse()

    def FailJob(self, request, context):
        return FailJobResponse()

    def ThrowError(self, request, context):
        return ThrowErrorResponse()

    def CreateWorkflowInstance(self, request, context):
        # context.set_code(grpc.StatusCode.NOT_FOUND)
        return CreateWorkflowInstanceResponse(workflowKey=randint(0, RANDOM_RANGE),
                                              bpmnProcessId=request.bpmnProcessId,
                                              version=request.version, workflowInstanceKey=randint(0, RANDOM_RANGE))

    def CreateWorkflowInstanceWithResult(self, request, context):
        return CreateWorkflowInstanceWithResultResponse(workflowKey=request.request.workflowKey,
                                                        bpmnProcessId=request.request.bpmnProcessId,
                                                        version=randint(0, 10), variables=request.request.variables)

    def CancelWorkflowInstance(self, request, context):
        return CancelWorkflowInstanceResponse()

    def DeployWorkflow(self, request, context):
        workflows = []
        for workflow in request.workflows:
            workflow_metadata = WorkflowMetadata(bpmnProcessId=str(uuid4()), version=randint(0, 10),
                                                 workflowKey=randint(0, RANDOM_RANGE), resourceName=workflow.name)
            workflows.append(workflow_metadata)
            deployed_workflows[workflow_metadata.bpmnProcessId] = workflow_metadata

        return DeployWorkflowResponse(key=randint(0, RANDOM_RANGE), workflows=workflows)

    def PublishMessage(self, request, context):
        return PublishMessageResponse()
