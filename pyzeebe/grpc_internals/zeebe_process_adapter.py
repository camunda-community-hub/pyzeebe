from __future__ import annotations

import json
import os
from collections.abc import Iterable
from typing import Callable, NoReturn

import anyio
import grpc

from pyzeebe.errors import (
    DecisionNotFoundError,
    InvalidJSONError,
    ProcessDefinitionHasNoStartEventError,
    ProcessDefinitionNotFoundError,
    ProcessInstanceNotFoundError,
    ProcessInvalidError,
    ProcessTimeoutError,
)
from pyzeebe.grpc_internals.grpc_utils import is_error_status
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.proto.gateway_pb2 import (
    CancelProcessInstanceRequest,
    CreateProcessInstanceRequest,
    CreateProcessInstanceWithResultRequest,
    DecisionMetadata,
    DecisionRequirementsMetadata,
    DeployResourceRequest,
    EvaluatedDecision,
    EvaluatedDecisionInput,
    EvaluatedDecisionOutput,
    EvaluateDecisionRequest,
    FormMetadata,
    MatchedDecisionRule,
    ProcessMetadata,
    Resource,
)
from pyzeebe.types import Variables

from .types import (
    CancelProcessInstanceResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    DeployResourceResponse,
    EvaluateDecisionResponse,
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
                    tenantId=tenant_id,  # type: ignore[arg-type]
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
                        tenantId=tenant_id,  # type: ignore[arg-type]
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

    async def deploy_resource(
        self, *resource_file_path: str | os.PathLike[str], tenant_id: str | None = None
    ) -> DeployResourceResponse:
        try:
            response = await self._gateway_stub.DeployResource(
                DeployResourceRequest(
                    resources=[await result for result in map(_create_resource_request, resource_file_path)],
                    tenantId=tenant_id,  # type: ignore[arg-type]
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

    async def evaluate_decision(
        self,
        decision_key: int | None,
        decision_id: str | None,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> EvaluateDecisionResponse:
        if decision_id is None and decision_key is None:
            raise ValueError("decision_key or decision_id must be not None")

        try:
            response = await self._gateway_stub.EvaluateDecision(
                EvaluateDecisionRequest(
                    decisionKey=decision_key,  # type: ignore[arg-type]
                    decisionId=decision_id,  # type: ignore[arg-type]
                    variables=json.dumps(variables),
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            # deprecated, used in camunda below 8.8
            if is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT) and (details := grpc_error.details()):
                if "but no decision found for" in details:
                    raise DecisionNotFoundError(decision_id=decision_id, decision_key=decision_key) from grpc_error
            # camunda 8.8+
            elif is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise DecisionNotFoundError(decision_id=decision_id, decision_key=decision_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

        return EvaluateDecisionResponse(
            decision_key=response.decisionKey,
            decision_id=response.decisionId,
            decision_name=response.decisionName,
            decision_version=response.decisionVersion,
            decision_requirements_id=response.decisionRequirementsId,
            decision_requirements_key=response.decisionRequirementsKey,
            decision_output=json.loads(response.decisionOutput),
            evaluated_decisions=[
                self._create_evaluated_decision_from_raw(evaluated_decision)
                for evaluated_decision in response.evaluatedDecisions
            ],
            failed_decision_id=response.failedDecisionId,
            failure_message=response.failureMessage,
            tenant_id=response.tenantId,
            decision_instance_key=response.decisionInstanceKey,
        )

    def _create_evaluated_decision_from_raw(
        self, response: EvaluatedDecision
    ) -> EvaluateDecisionResponse.EvaluatedDecision:
        return EvaluateDecisionResponse.EvaluatedDecision(
            decision_key=response.decisionKey,
            decision_id=response.decisionId,
            decision_name=response.decisionName,
            decision_version=response.decisionVersion,
            decision_type=response.decisionType,
            decision_output=json.loads(response.decisionOutput),
            matched_rules=[self._create_matched_rule_from_raw(matched_rule) for matched_rule in response.matchedRules],
            evaluated_inputs=[
                self._create_evaluated_input_from_raw(evaluated_input) for evaluated_input in response.evaluatedInputs
            ],
            tenant_id=response.tenantId,
        )

    def _create_matched_rule_from_raw(
        self, response: MatchedDecisionRule
    ) -> EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule:
        return EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule(
            rule_id=response.ruleId,
            rule_index=response.ruleIndex,
            evaluated_outputs=[
                self._create_evaluated_output_from_raw(evaluated_output)
                for evaluated_output in response.evaluatedOutputs
            ],
        )

    def _create_evaluated_input_from_raw(
        self, response: EvaluatedDecisionInput
    ) -> EvaluateDecisionResponse.EvaluatedDecision.EvaluatedDecisionInput:
        return EvaluateDecisionResponse.EvaluatedDecision.EvaluatedDecisionInput(
            input_id=response.inputId,
            input_name=response.inputName,
            input_value=json.loads(response.inputValue),
        )

    def _create_evaluated_output_from_raw(
        self, response: EvaluatedDecisionOutput
    ) -> EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule.EvaluatedDecisionOutput:
        return EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule.EvaluatedDecisionOutput(
            output_id=response.outputId,
            output_name=response.outputName,
            output_value=json.loads(response.outputValue),
        )


_METADATA_PARSERS: dict[
    str,
    Callable[[ProcessMetadata], DeployResourceResponse.ProcessMetadata]
    | Callable[[DecisionMetadata], DeployResourceResponse.DecisionMetadata]
    | Callable[[DecisionRequirementsMetadata], DeployResourceResponse.DecisionRequirementsMetadata]
    | Callable[[FormMetadata], DeployResourceResponse.FormMetadata],
] = {
    "process": ZeebeProcessAdapter._create_process_from_raw_process,
    "decision": ZeebeProcessAdapter._create_decision_from_raw_decision,
    "decisionRequirements": ZeebeProcessAdapter._create_decision_requirements_from_raw_decision_requirements,
    "form": ZeebeProcessAdapter._create_form_from_raw_form,
}


async def _create_resource_request(resource_file_path: str | os.PathLike[str]) -> Resource:
    async with await anyio.open_file(resource_file_path, "rb") as file:
        return Resource(name=os.path.basename(resource_file_path), content=await file.read())
