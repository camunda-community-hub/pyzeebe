import json
import os
from typing import Dict, Tuple

import aiofiles
import grpc
from zeebe_grpc.gateway_pb2 import (CancelProcessInstanceRequest,
                                    CreateProcessInstanceRequest,
                                    CreateProcessInstanceWithResultRequest,
                                    DeployProcessRequest,
                                    DeployProcessResponse,
                                    ProcessRequestObject)

from pyzeebe.errors import (InvalidJSONError,
                            ProcessDefinitionHasNoStartEventError,
                            ProcessDefinitionNotFoundError,
                            ProcessInstanceNotFoundError, ProcessInvalidError,
                            ProcessTimeoutError)
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase


class ZeebeProcessAdapter(ZeebeAdapterBase):
    async def create_process_instance(self, bpmn_process_id: str, version: int, variables: Dict) -> int:
        try:
            response = await self._gateway_stub.CreateProcessInstance(
                CreateProcessInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                             variables=json.dumps(variables)))
        except grpc.aio.AioRpcError as rpc_error:
            await self._create_process_errors(rpc_error, bpmn_process_id, version, variables)
        return response.processInstanceKey

    async def create_process_instance_with_result(self, bpmn_process_id: str, version: int, variables: Dict,
                                                  timeout: int, variables_to_fetch) -> Tuple[int, Dict]:
        try:
            response = await self._gateway_stub.CreateProcessInstanceWithResult(
                CreateProcessInstanceWithResultRequest(
                    request=CreateProcessInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                                         variables=json.dumps(variables)),
                    requestTimeout=timeout, fetchVariables=variables_to_fetch))
        except grpc.aio.AioRpcError as rpc_error:
            await self._create_process_errors(rpc_error, bpmn_process_id, version, variables)
        return response.processInstanceKey, json.loads(response.variables)

    async def _create_process_errors(self, rpc_error: grpc.aio.AioRpcError, bpmn_process_id: str, version: int,
                                     variables: Dict) -> None:
        if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
            raise ProcessDefinitionNotFoundError(
                bpmn_process_id=bpmn_process_id, version=version) from rpc_error
        elif self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
            raise InvalidJSONError(
                f"Cannot start process: {bpmn_process_id} with version {version}. Variables: {variables}") from rpc_error
        elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
            raise ProcessDefinitionHasNoStartEventError(bpmn_process_id=bpmn_process_id) from rpc_error
        elif self.is_error_status(rpc_error, grpc.StatusCode.DEADLINE_EXCEEDED):
            raise ProcessTimeoutError(bpmn_process_id) from rpc_error
        else:
            await self._common_zeebe_grpc_errors(rpc_error)

    async def cancel_process_instance(self, process_instance_key: int) -> None:
        try:
            await self._gateway_stub.CancelProcessInstance(
                CancelProcessInstanceRequest(processInstanceKey=process_instance_key))
        except grpc.aio.AioRpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise ProcessInstanceNotFoundError(
                    process_instance_key=process_instance_key)
            else:
                await self._common_zeebe_grpc_errors(rpc_error)

    async def deploy_process(self, *process_file_path: str) -> DeployProcessResponse:
        try:
            return await self._gateway_stub.DeployProcess(
                DeployProcessRequest(processes=[await result for result in map(self._get_process_request_object,
                                                                               process_file_path)]))
        except grpc.aio.AioRpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ProcessInvalidError()
            else:
                await self._common_zeebe_grpc_errors(rpc_error)

    @staticmethod
    async def _get_process_request_object(process_file_path: str) -> ProcessRequestObject:
        async with aiofiles.open(process_file_path, "rb") as file:
            return ProcessRequestObject(name=os.path.basename(process_file_path),
                                        definition=await file.read())
