from __future__ import annotations

import json
import os
from collections.abc import Iterable
from typing import Callable, NoReturn

import anyio
import grpc
from zeebe_grpc.gateway_pb2 import (
    CancelProcessInstanceRequest,
    CreateProcessInstanceRequest,
    CreateProcessInstanceWithResultRequest,
    DecisionMetadata,
    DecisionRequirementsMetadata,
    DeployResourceRequest,
    FormMetadata,
    ProcessMetadata,
    Resource,
)

from pyzeebe.errors import (
    InvalidJSONError,
    ProcessDefinitionHasNoStartEventError,
    ProcessDefinitionNotFoundError,
    ProcessInstanceNotFoundError,
    ProcessInvalidError,
    ProcessTimeoutError,
)
from pyzeebe.grpc_internals.grpc_utils import is_error_status
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.types import Variables

from .types import (
    CancelProcessInstanceResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    DeployResourceResponse,
)


class ZeebeProcessAdapter(ZeebeAdapterBase):
    async def create_process_instance(
        self,
        bpmn_process_id: str,
        version: int,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceResponse:
        try:
            response = await self._gateway_stub.CreateProcessInstance(
                CreateProcessInstanceRequest(
                    bpmnProcessId=bpmn_process_id,
                    version=version,
                    variables=json.dumps(variables),
                    tenantId=tenant_id,
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            await self._create_process_errors(grpc_error, bpmn_process_id, version, variables)

        return CreateProcessInstanceResponse(
            process_definition_key=response.processDefinitionKey,
            bpmn_process_id=response.bpmnProcessId,
            version=response.version,
            process_instance_key=response.processInstanceKey,
            tenant_id=response.tenantId,
        )

    async def create_process_instance_with_result(
        self,
        bpmn_process_id: str,
        version: int,
        variables: Variables,
        timeout: int,  # noqa: ASYNC109
        variables_to_fetch: Iterable[str],
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceWithResultResponse:
        try:
            response = await self._gateway_stub.CreateProcessInstanceWithResult(
                CreateProcessInstanceWithResultRequest(
                    request=CreateProcessInstanceRequest(
                        bpmnProcessId=bpmn_process_id,
                        version=version,
                        variables=json.dumps(variables),
                        tenantId=tenant_id,
                    ),
                    requestTimeout=timeout,
                    fetchVariables=variables_to_fetch,
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            await self._create_process_errors(grpc_error, bpmn_process_id, version, variables)

        return CreateProcessInstanceWithResultResponse(
            process_definition_key=response.processDefinitionKey,
            bpmn_process_id=response.bpmnProcessId,
            version=response.version,
            process_instance_key=response.processInstanceKey,
            variables=json.loads(response.variables),
            tenant_id=response.tenantId,
        )

    async def _create_process_errors(
        self, grpc_error: grpc.aio.AioRpcError, bpmn_process_id: str, version: int, variables: Variables
    ) -> NoReturn:
        if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
            raise ProcessDefinitionNotFoundError(bpmn_process_id=bpmn_process_id, version=version) from grpc_error
        elif is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT):
            raise InvalidJSONError(
                f"Cannot start process: {bpmn_process_id} with version {version}. Variables: {variables}"
            ) from grpc_error
        elif is_error_status(grpc_error, grpc.StatusCode.FAILED_PRECONDITION):
            raise ProcessDefinitionHasNoStartEventError(bpmn_process_id=bpmn_process_id) from grpc_error
        elif is_error_status(grpc_error, grpc.StatusCode.DEADLINE_EXCEEDED):
            raise ProcessTimeoutError(bpmn_process_id) from grpc_error
        await self._handle_grpc_error(grpc_error)

    async def cancel_process_instance(self, process_instance_key: int) -> CancelProcessInstanceResponse:
        try:
            await self._gateway_stub.CancelProcessInstance(
                CancelProcessInstanceRequest(processInstanceKey=process_instance_key)
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise ProcessInstanceNotFoundError(process_instance_key=process_instance_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

        return CancelProcessInstanceResponse()

    async def deploy_resource(self, *resource_file_path: str, tenant_id: str | None = None) -> DeployResourceResponse:
        try:
            response = await self._gateway_stub.DeployResource(
                DeployResourceRequest(
                    resources=[await result for result in map(_create_resource_request, resource_file_path)],
                    tenantId=tenant_id,
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ProcessInvalidError() from grpc_error
            await self._handle_grpc_error(grpc_error)

        deployments: list[
            DeployResourceResponse.ProcessMetadata
            | DeployResourceResponse.DecisionMetadata
            | DeployResourceResponse.DecisionRequirementsMetadata
            | DeployResourceResponse.FormMetadata
        ] = []
        for deployment in response.deployments:
            metadata_field = deployment.WhichOneof("Metadata")
            metadata = getattr(deployment, metadata_field)
            deployments.append(_METADATA_PARSERS[metadata_field](metadata))

        return DeployResourceResponse(
            key=response.key,
            deployments=deployments,
            tenant_id=response.tenantId,
        )

    @staticmethod
    def _create_process_from_raw_process(response: ProcessMetadata) -> DeployResourceResponse.ProcessMetadata:
        return DeployResourceResponse.ProcessMetadata(
            bpmn_process_id=response.bpmnProcessId,
            version=response.version,
            process_definition_key=response.processDefinitionKey,
            resource_name=response.resourceName,
            tenant_id=response.tenantId,
        )

    @staticmethod
    def _create_decision_from_raw_decision(response: DecisionMetadata) -> DeployResourceResponse.DecisionMetadata:
        return DeployResourceResponse.DecisionMetadata(
            dmn_decision_id=response.dmnDecisionId,
            dmn_decision_name=response.dmnDecisionName,
            version=response.version,
            decision_key=response.decisionKey,
            dmn_decision_requirements_id=response.dmnDecisionRequirementsId,
            decision_requirements_key=response.decisionRequirementsKey,
            tenant_id=response.tenantId,
        )

    @staticmethod
    def _create_decision_requirements_from_raw_decision_requirements(
        response: DecisionRequirementsMetadata,
    ) -> DeployResourceResponse.DecisionRequirementsMetadata:
        return DeployResourceResponse.DecisionRequirementsMetadata(
            dmn_decision_requirements_id=response.dmnDecisionRequirementsId,
            dmn_decision_requirements_name=response.dmnDecisionRequirementsName,
            version=response.version,
            decision_requirements_key=response.decisionRequirementsKey,
            resource_name=response.resourceName,
            tenant_id=response.tenantId,
        )

    @staticmethod
    def _create_form_from_raw_form(response: FormMetadata) -> DeployResourceResponse.FormMetadata:
        return DeployResourceResponse.FormMetadata(
            form_id=response.formId,
            version=response.version,
            form_key=response.formKey,
            resource_name=response.resourceName,
            tenant_id=response.tenantId,
        )


_METADATA_PARSERS: dict[
    str,
    Callable[
        [ProcessMetadata | DecisionMetadata | DecisionRequirementsMetadata | FormMetadata],
        DeployResourceResponse.ProcessMetadata
        | DeployResourceResponse.DecisionMetadata
        | DeployResourceResponse.DecisionRequirementsMetadata
        | DeployResourceResponse.FormMetadata,
    ],
] = {
    "process": ZeebeProcessAdapter._create_process_from_raw_process,
    "decision": ZeebeProcessAdapter._create_decision_from_raw_decision,
    "decisionRequirements": ZeebeProcessAdapter._create_decision_requirements_from_raw_decision_requirements,
    "form": ZeebeProcessAdapter._create_form_from_raw_form,
}


async def _create_resource_request(resource_file_path: str) -> Resource:
    async with await anyio.open_file(resource_file_path, "rb") as file:
        return Resource(name=os.path.basename(resource_file_path), content=await file.read())
