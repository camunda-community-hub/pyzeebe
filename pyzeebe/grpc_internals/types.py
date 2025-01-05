from __future__ import annotations

from dataclasses import dataclass

from pyzeebe.types import Variables


@dataclass(frozen=True)
class CreateProcessInstanceResponse:
    process_definition_key: int
    """the key of the process definition which was used to create the process instance"""
    bpmn_process_id: str
    """the BPMN process ID of the process definition which was used to create the process
    instance
    """
    version: int
    """the version of the process definition which was used to create the process instance"""
    process_instance_key: int
    """the unique identifier of the created process instance; to be used wherever a request
    needs a process instance key (e.g. CancelProcessInstanceRequest)
    """
    tenant_id: str | None
    """the tenant ID of the created process instance"""


@dataclass(frozen=True)
class CreateProcessInstanceWithResultResponse:
    process_definition_key: int
    """the key of the process definition which was used to create the process instance"""
    bpmn_process_id: str
    """the BPMN process ID of the process definition which was used to create the process
    instance
    """
    version: int
    """the version of the process definition which was used to create the process instance"""
    process_instance_key: int
    """the unique identifier of the created process instance; to be used wherever a request
    needs a process instance key (e.g. CancelProcessInstanceRequest)
    """
    variables: Variables
    """consisting of all visible variables to the root scope"""
    tenant_id: str | None
    """the tenant ID of the created process instance"""


@dataclass(frozen=True)
class CancelProcessInstanceResponse:
    pass


@dataclass(frozen=True)
class DeployResourceResponse:
    @dataclass(frozen=True)
    class ProcessMetadata:
        bpmn_process_id: str
        """the bpmn process ID, as parsed during deployment; together with the version forms a
        unique identifier for a specific process definition
        """
        version: int
        """the assigned process version"""
        process_definition_key: int
        """the assigned key, which acts as a unique identifier for this process"""
        resource_name: str
        """the resource name from which this process was parsed"""
        tenant_id: str | None
        """the tenant ID of the deployed process"""

    @dataclass(frozen=True)
    class DecisionMetadata:
        dmn_decision_id: str
        """the dmn decision ID, as parsed during deployment; together with the
        versions forms a unique identifier for a specific decision
        """
        dmn_decision_name: str
        """the dmn name of the decision, as parsed during deployment"""
        version: int
        """the assigned decision version"""
        decision_key: int
        """the assigned decision key, which acts as a unique identifier for this
        decision
        """
        dmn_decision_requirements_id: str
        """the dmn ID of the decision requirements graph that this decision is part
        of, as parsed during deployment
        """
        decision_requirements_key: int
        """the assigned key of the decision requirements graph that this decision is
        part of
        """
        tenant_id: str | None
        """the tenant ID of the deployed decision"""

    @dataclass(frozen=True)
    class DecisionRequirementsMetadata:
        dmn_decision_requirements_id: str
        """the dmn decision requirements ID, as parsed during deployment; together
        with the versions forms a unique identifier for a specific decision
        """
        dmn_decision_requirements_name: str
        """the dmn name of the decision requirements, as parsed during deployment"""
        version: int
        """the assigned decision requirements version"""
        decision_requirements_key: int
        """the assigned decision requirements key, which acts as a unique identifier
        for this decision requirements
        """
        resource_name: str
        """the resource name from which this decision
        requirements was parsed
        """
        tenant_id: str | None
        """the tenant ID of the deployed decision requirements"""

    @dataclass(frozen=True)
    class FormMetadata:
        form_id: str
        """the form ID, as parsed during deployment; together with the
        versions forms a unique identifier for a specific form
        """
        version: int
        """the assigned form version"""
        form_key: int
        """the assigned key, which acts as a unique identifier for this form"""
        resource_name: str
        """the resource name"""
        tenant_id: str | None
        """the tenant ID of the deployed form"""

    key: int
    """the unique key identifying the deployment"""
    deployments: list[ProcessMetadata | DecisionMetadata | DecisionRequirementsMetadata | FormMetadata]
    """a list of deployed resources, e.g. processes"""
    tenant_id: str | None
    """the tenant ID of the deployed resources"""


@dataclass(frozen=True)
class BroadcastSignalResponse:
    key: int
    """the unique ID of the signal that was broadcasted"""
    tenant_id: str | None
    """the tenant ID of the signal that was broadcasted"""


@dataclass(frozen=True)
class PublishMessageResponse:
    key: int
    """the unique ID of the message that was published"""
    tenant_id: str | None
    """the tenant ID of the message"""


@dataclass(frozen=True)
class CompleteJobResponse:
    pass


@dataclass(frozen=True)
class FailJobResponse:
    pass


@dataclass(frozen=True)
class ThrowErrorResponse:
    pass
