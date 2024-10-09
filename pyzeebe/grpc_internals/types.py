from __future__ import annotations

from dataclasses import dataclass

from pyzeebe.types import Variables


@dataclass(frozen=True)
class CreateProcessInstanceResponse:
    #: the key of the process definition which was used to create the process instance
    process_definition_key: int
    #: the BPMN process ID of the process definition which was used to create the process
    #: instance
    bpmn_process_id: str
    #: the version of the process definition which was used to create the process instance
    version: int
    #: the unique identifier of the created process instance; to be used wherever a request
    #: needs a process instance key (e.g. CancelProcessInstanceRequest)
    process_instance_key: int
    #: the tenant ID of the created process instance
    tenant_id: str | None


@dataclass(frozen=True)
class CreateProcessInstanceWithResultResponse:
    #: the key of the process definition which was used to create the process instance
    process_definition_key: int
    #: the BPMN process ID of the process definition which was used to create the process
    #: instance
    bpmn_process_id: str
    #: the version of the process definition which was used to create the process instance
    version: int
    #: the unique identifier of the created process instance; to be used wherever a request
    #: needs a process instance key (e.g. CancelProcessInstanceRequest)
    process_instance_key: int
    #: consisting of all visible variables to the root scope
    variables: Variables
    #: the tenant ID of the process definition
    tenant_id: str | None


@dataclass(frozen=True)
class CancelProcessInstanceResponse:
    pass


@dataclass(frozen=True)
class DeployResourceResponse:
    @dataclass(frozen=True)
    class ProcessMetadata:
        #: the bpmn process ID, as parsed during deployment; together with the version forms a
        #: unique identifier for a specific process definition
        bpmn_process_id: str
        #: the assigned process version
        version: int
        #: the assigned key, which acts as a unique identifier for this process
        process_definition_key: int
        #: the resource name (see: ProcessRequestObject.name) from which this process was
        #: parsed
        resource_name: str
        #: the tenant ID of the deployed process
        tenant_id: str | None

    @dataclass(frozen=True)
    class DecisionMetadata:
        #: the dmn decision ID, as parsed during deployment; together with the
        #: versions forms a unique identifier for a specific decision
        dmn_decision_id: str
        #: the dmn name of the decision, as parsed during deployment
        dmn_decision_name: str
        #: the assigned decision version
        version: int
        #: the assigned decision key, which acts as a unique identifier for this
        #: decision
        decision_key: int
        #: the dmn ID of the decision requirements graph that this decision is part
        #: of, as parsed during deployment
        dmn_decision_requirements_id: str
        #: the assigned key of the decision requirements graph that this decision is
        #: part of
        decision_requirements_key: int
        #: the tenant ID of the deployed decision
        tenant_id: str | None

    @dataclass(frozen=True)
    class DecisionRequirementsMetadata:
        #: the dmn decision requirements ID, as parsed during deployment; together
        #: with the versions forms a unique identifier for a specific decision
        dmn_decision_requirements_id: str
        #: the dmn name of the decision requirements, as parsed during deployment
        dmn_decision_requirements_name: str
        #: the assigned decision requirements version
        version: int
        #: the assigned decision requirements key, which acts as a unique identifier
        #: for this decision requirements
        decision_requirements_key: int
        #: the resource name (see: Resource.name) from which this decision
        #: requirements was parsed
        resource_name: str
        #: the tenant ID of the deployed decision requirements
        tenant_id: str | None

    @dataclass(frozen=True)
    class FormMetadata:
        #: the form ID, as parsed during deployment; together with the
        #: versions forms a unique identifier for a specific form
        form_id: str
        #: the assigned form version
        version: int
        #: the assigned key, which acts as a unique identifier for this form
        form_key: int
        #: the resource name
        resource_name: str
        #: the tenant ID of the deployed form
        tenant_id: str | None

    #: the unique key identifying the deployment
    key: int
    #: a list of deployed resources, e.g. processes
    deployments: list[ProcessMetadata | DecisionMetadata | DecisionRequirementsMetadata | FormMetadata]
    #: the tenant ID of the deployed resources
    tenant_id: str | None


@dataclass(frozen=True)
class PublishMessageResponse:
    #: the unique ID of the message that was published
    key: int
    #: the tenant ID of the message
    tenant_id: str | None


@dataclass(frozen=True)
class CompleteJobResponse:
    pass


@dataclass(frozen=True)
class FailJobResponse:
    pass


@dataclass(frozen=True)
class ThrowErrorResponse:
    pass
