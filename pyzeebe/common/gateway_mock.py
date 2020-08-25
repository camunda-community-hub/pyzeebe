from random import randint
from typing import List
from unittest.mock import patch
from uuid import uuid4

import grpc

from pyzeebe.common.random_utils import RANDOM_RANGE
from pyzeebe.grpc_internals.zeebe_pb2 import *
from pyzeebe.grpc_internals.zeebe_pb2_grpc import GatewayServicer


@patch('grpc.insecure_channel')
def mock_channel():
    pass


class GatewayMock(GatewayServicer):
    # TODO: Mock behaviour of zeebe

    def __init__(self):
        self.deployed_workflows = {}
        self.active_jobs = {}

    def CompleteJob(self, request, context):
        return CompleteJobResponse()

    def FailJob(self, request, context):
        return FailJobResponse()

    def ThrowError(self, request, context):
        self.active_jobs[request.jobKey]['error'] = True
        return ThrowErrorResponse()

    def CreateWorkflowInstance(self, request, context):
        if request.bpmnProcessId in self.deployed_workflows.keys():
            return CreateWorkflowInstanceResponse(workflowKey=randint(0, RANDOM_RANGE),
                                                  bpmnProcessId=request.bpmnProcessId,
                                                  version=request.version, workflowInstanceKey=randint(0, RANDOM_RANGE))
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CreateWorkflowInstanceResponse()

    def CreateWorkflowInstanceWithResult(self, request, context):
        if request.request.bpmnProcessId in self.deployed_workflows.keys():
            return CreateWorkflowInstanceWithResultResponse(workflowKey=request.request.workflowKey,
                                                            bpmnProcessId=request.request.bpmnProcessId,
                                                            version=randint(0, 10), variables=request.request.variables)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CreateWorkflowInstanceWithResultResponse()

    def CancelWorkflowInstance(self, request, context):
        return CancelWorkflowInstanceResponse()

    def DeployWorkflow(self, request, context):
        workflows = []
        for workflow in request.workflows:
            workflow_metadata = WorkflowMetadata(bpmnProcessId=str(uuid4()), version=randint(0, 10),
                                                 workflowKey=randint(0, RANDOM_RANGE), resourceName=workflow.name)
            workflows.append(workflow_metadata)

        return DeployWorkflowResponse(key=randint(0, RANDOM_RANGE), workflows=workflows)

    def PublishMessage(self, request, context):
        return PublishMessageResponse()

    def mock_deploy_workflow(self, bpmn_process_id: str, version: int, tasks: List[str]):
        self.deployed_workflows[bpmn_process_id] = {'bpmn_process_id': bpmn_process_id, 'version': version,
                                                    'tasks': tasks}
