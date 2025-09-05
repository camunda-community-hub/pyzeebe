from __future__ import annotations

import enum
from dataclasses import dataclass

from pyzeebe.types import JsonType, Variables


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
class EvaluateDecisionResponse:

    @dataclass(frozen=True)
    class EvaluatedDecision:

        @dataclass(frozen=True)
        class MatchedDecisionRule:

            @dataclass(frozen=True)
            class EvaluatedDecisionOutput:
                output_id: str
                """the id of the evaluated decision output"""
                output_name: str
                """the name of the evaluated decision output"""
                output_value: JsonType
                """the value of the evaluated decision output"""

            rule_id: str
            """the id of the matched rule"""
            rule_index: int
            """the index of the matched rule"""
            evaluated_outputs: list[EvaluatedDecisionOutput]
            """the evaluated decision outputs"""

        @dataclass(frozen=True)
        class EvaluatedDecisionInput:
            input_id: str
            """the id of the evaluated decision input"""
            input_name: str
            """the name of the evaluated decision input"""
            input_value: JsonType
            """the value of the evaluated decision input"""

        decision_key: int
        """the unique key identifying the decision which was evaluated (e.g. returned
        from a decision in the DeployResourceResponse message)
        """
        decision_id: str
        """the ID of the decision which was evaluated"""
        decision_name: str
        """the name of the decision which was evaluated"""
        decision_version: int
        """the version of the decision which was evaluated"""
        decision_type: str
        """the type of the decision which was evaluated"""
        decision_output: JsonType
        """JSON document that will instantiate the result of the decision which was
        evaluated; it will be a JSON object, as the result output will be mapped
        in a key-value fashion, e.g. { "a": 1 }.
        """
        matched_rules: list[MatchedDecisionRule]
        """the decision rules that matched within this decision evaluation"""
        evaluated_inputs: list[EvaluatedDecisionInput]
        """the decision inputs that were evaluated within this decision evaluation"""
        tenant_id: str | None
        """the tenant identifier of the evaluated decision"""

    decision_key: int
    """the unique key identifying the decision which was evaluated (e.g. returned
    from a decision in the DeployResourceResponse message)
    """
    decision_id: str
    """the ID of the decision which was evaluated"""
    decision_name: str
    """the name of the decision which was evaluated"""
    decision_version: int
    """the version of the decision which was evaluated"""
    decision_requirements_id: str
    """the ID of the decision requirements graph that the decision which was
    evaluated is part of.
    """
    decision_requirements_key: int
    """the unique key identifying the decision requirements graph that the
    decision which was evaluated is part of.
    """
    decision_output: JsonType
    """JSON document that will instantiate the result of the decision which was
    evaluated; it will be a JSON object, as the result output will be mapped
    in a key-value fashion, e.g. { "a": 1 }.
    """
    evaluated_decisions: list[EvaluatedDecision]
    """a list of decisions that were evaluated within the requested decision evaluation"""
    failed_decision_id: str
    """an optional string indicating the ID of the decision which
    failed during evaluation
    """
    failure_message: str
    """an optional message describing why the decision which was evaluated failed"""
    tenant_id: str | None
    """the tenant identifier of the evaluated decision"""
    decision_instance_key: int
    """the unique key identifying this decision evaluation"""


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


@dataclass(frozen=True)
class UpdateJobTimeoutResponse:
    pass


@dataclass(frozen=True)
class TopologyResponse:

    @dataclass(frozen=True)
    class BrokerInfo:

        @dataclass(frozen=True)
        class Partition:

            class PartitionBrokerRole(enum.IntEnum):
                """Describes the Raft role of the broker for a given partition"""

                LEADER = 0
                FOLLOWER = 1
                INACTIVE = 2

            class PartitionBrokerHealth(enum.IntEnum):
                """Describes the current health of the partition"""

                HEALTHY = 0
                UNHEALTHY = 1
                DEAD = 2

            partition_id: int
            """the unique ID of this partition"""
            role: PartitionBrokerRole
            """the role of the broker for this partition"""
            health: PartitionBrokerHealth
            """the health of this partition"""

        node_id: int
        """unique (within a cluster) node ID for the broker"""
        host: str
        """hostname of the broker"""
        port: int
        """port for the broker"""
        partitions: list[Partition]
        """list of partitions managed or replicated on this broker"""
        version: str
        """broker version"""

    brokers: list[BrokerInfo]
    """list of brokers part of this cluster"""
    cluster_size: int
    """how many nodes are in the cluster"""
    partitions_count: int
    """how many partitions are spread across the cluster"""
    replication_factor: int
    """configured replication factor for this cluster"""
    gateway_version: str
    """gateway version"""


@dataclass(frozen=True)
class HealthCheckResponse:
    """GRPC Health Checking Protocol

    https://grpc.io/docs/guides/health-checking/
    """

    class ServingStatus(enum.IntEnum):
        UNKNOWN = 0
        SERVING = 1
        NOT_SERVING = 2
        SERVICE_UNKNOWN = 3

    status: ServingStatus
