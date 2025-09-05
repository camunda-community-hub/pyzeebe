from collections.abc import Callable
from typing import Any

from pyzeebe.adapters.types import (
    DeployResourceResponse,
)
from pyzeebe.proto.gateway_pb2 import (
    DecisionMetadata,
    DecisionRequirementsMetadata,
    FormMetadata,
    ProcessMetadata,
)


def _create_process_from_raw_process(response: ProcessMetadata) -> DeployResourceResponse.ProcessMetadata:
    return DeployResourceResponse.ProcessMetadata(
        bpmn_process_id=response.bpmnProcessId,
        version=response.version,
        process_definition_key=response.processDefinitionKey,
        resource_name=response.resourceName,
        tenant_id=response.tenantId,
    )


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
    Callable[[ProcessMetadata], DeployResourceResponse.ProcessMetadata]
    | Callable[[DecisionMetadata], DeployResourceResponse.DecisionMetadata]
    | Callable[[DecisionRequirementsMetadata], DeployResourceResponse.DecisionRequirementsMetadata]
    | Callable[[FormMetadata], DeployResourceResponse.FormMetadata],
] = {
    "process": _create_process_from_raw_process,
    "decision": _create_decision_from_raw_decision,
    "decisionRequirements": _create_decision_requirements_from_raw_decision_requirements,
    "form": _create_form_from_raw_form,
}


def parse_resource_metadata(
    field: str, data: ProcessMetadata | DecisionMetadata | DecisionRequirementsMetadata | FormMetadata
) -> Any:
    return _METADATA_PARSERS[field](data)  # type: ignore
