import json
import os
from typing import Dict

import grpc
from zeebe_grpc.gateway_pb2 import CreateWorkflowInstanceRequest, CreateWorkflowInstanceWithResultRequest, \
    CancelWorkflowInstanceRequest, WorkflowRequestObject, DeployWorkflowRequest, DeployWorkflowResponse

from pyzeebe.errors import InvalidJSONError, WorkflowNotFoundError, WorkflowInstanceNotFoundError, WorkflowHasNoStartEventError, \
    WorkflowInvalidError
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase


class ZeebeWorkflowAdapter(ZeebeAdapterBase):
    def create_workflow_instance(self, bpmn_process_id: str, version: int, variables: Dict) -> int:
        try:
            response = self._gateway_stub.CreateWorkflowInstance(
                CreateWorkflowInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                              variables=json.dumps(variables)))
            return response.workflowInstanceKey
        except grpc.RpcError as rpc_error:
            self._create_workflow_errors(rpc_error, bpmn_process_id, version, variables)

    def create_workflow_instance_with_result(self, bpmn_process_id: str, version: int, variables: Dict,
                                             timeout: int, variables_to_fetch) -> Dict:
        try:
            response = self._gateway_stub.CreateWorkflowInstanceWithResult(
                CreateWorkflowInstanceWithResultRequest(
                    request=CreateWorkflowInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                                          variables=json.dumps(variables)),
                    requestTimeout=timeout, fetchVariables=variables_to_fetch))
            return json.loads(response.variables)
        except grpc.RpcError as rpc_error:
            self._create_workflow_errors(rpc_error, bpmn_process_id, version, variables)

    def _create_workflow_errors(self, rpc_error: grpc.RpcError, bpmn_process_id: str, version: int,
                                variables: Dict) -> None:
        if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
            raise WorkflowNotFoundError(bpmn_process_id=bpmn_process_id, version=version)
        elif self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
            raise InvalidJSONError(
                f"Cannot start workflow: {bpmn_process_id} with version {version}. Variables: {variables}")
        elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
            raise WorkflowHasNoStartEventError(bpmn_process_id=bpmn_process_id)
        else:
            self._common_zeebe_grpc_errors(rpc_error)

    def cancel_workflow_instance(self, workflow_instance_key: int) -> None:
        try:
            self._gateway_stub.CancelWorkflowInstance(
                CancelWorkflowInstanceRequest(workflowInstanceKey=workflow_instance_key))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise WorkflowInstanceNotFoundError(workflow_instance_key=workflow_instance_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def deploy_workflow(self, *workflow_file_path: str) -> DeployWorkflowResponse:
        try:
            return self._gateway_stub.DeployWorkflow(
                DeployWorkflowRequest(workflows=map(self._get_workflow_request_object, workflow_file_path)))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise WorkflowInvalidError()
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    @staticmethod
    def _get_workflow_request_object(workflow_file_path: str) -> WorkflowRequestObject:
        with open(workflow_file_path, "rb") as file:
            return WorkflowRequestObject(name=os.path.split(workflow_file_path)[-1],
                                         definition=file.read())
