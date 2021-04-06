import grpc
import json
import os
from typing import Dict, Tuple
from zeebe_grpc.gateway_pb2 import CreateProcessInstanceRequest, CreateProcessInstanceWithResultRequest, \
    CancelProcessInstanceRequest, ProcessRequestObject, DeployProcessRequest, DeployProcessResponse

from pyzeebe.errors import InvalidJSONError, ProcessDefinitionNotFoundError, ProcessInstanceNotFoundError, \
    ProcessHasNoStartEventError, ProcessInvalidError
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase


class ZeebeProcessAdapter(ZeebeAdapterBase):
    def create_process_instance(self, bpmn_process_id: str, version: int, variables: Dict) -> int:
        try:
            response = self._gateway_stub.CreateProcessInstance(
                CreateProcessInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                             variables=json.dumps(variables)))
            return response.processInstanceKey
        except grpc.RpcError as rpc_error:
            self._create_process_errors(
                rpc_error, bpmn_process_id, version, variables)

    def create_process_instance_with_result(self, bpmn_process_id: str, version: int, variables: Dict,
                                            timeout: int, variables_to_fetch) -> Tuple[int, Dict]:
        try:
            response = self._gateway_stub.CreateProcessInstanceWithResult(
                CreateProcessInstanceWithResultRequest(
                    request=CreateProcessInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                                         variables=json.dumps(variables)),
                    requestTimeout=timeout, fetchVariables=variables_to_fetch))
            return response.processInstanceKey, json.loads(response.variables)
        except grpc.RpcError as rpc_error:
            self._create_process_errors(
                rpc_error, bpmn_process_id, version, variables)

    def _create_process_errors(self, rpc_error: grpc.RpcError, bpmn_process_id: str, version: int,
                               variables: Dict) -> None:
        if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
            raise ProcessDefinitionNotFoundError(
                bpmn_process_id=bpmn_process_id, version=version)
        elif self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
            raise InvalidJSONError(
                f"Cannot start process: {bpmn_process_id} with version {version}. Variables: {variables}")
        elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
            raise ProcessHasNoStartEventError(bpmn_process_id=bpmn_process_id)
        else:
            self._common_zeebe_grpc_errors(rpc_error)

    def cancel_process_instance(self, process_instance_key: int) -> None:
        try:
            self._gateway_stub.CancelProcessInstance(
                CancelProcessInstanceRequest(processInstanceKey=process_instance_key))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise ProcessInstanceNotFoundError(
                    process_instance_key=process_instance_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def deploy_process(self, *process_file_path: str) -> DeployProcessResponse:
        try:
            return self._gateway_stub.DeployProcess(
                DeployProcessRequest(processes=map(self._get_process_request_object, process_file_path)))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ProcessInvalidError()
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    @staticmethod
    def _get_process_request_object(process_file_path: str) -> ProcessRequestObject:
        with open(process_file_path, "rb") as file:
            return ProcessRequestObject(name=os.path.split(process_file_path)[-1],
                                        definition=file.read())
