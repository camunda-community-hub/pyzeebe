from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreamActivatedJobsRequest(_message.Message):
    __slots__ = ("type", "worker", "timeout", "fetchVariable", "tenantIds")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WORKER_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    FETCHVARIABLE_FIELD_NUMBER: _ClassVar[int]
    TENANTIDS_FIELD_NUMBER: _ClassVar[int]
    type: str
    worker: str
    timeout: int
    fetchVariable: _containers.RepeatedScalarFieldContainer[str]
    tenantIds: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, type: _Optional[str] = ..., worker: _Optional[str] = ..., timeout: _Optional[int] = ..., fetchVariable: _Optional[_Iterable[str]] = ..., tenantIds: _Optional[_Iterable[str]] = ...) -> None: ...

class ActivateJobsRequest(_message.Message):
    __slots__ = ("type", "worker", "timeout", "maxJobsToActivate", "fetchVariable", "requestTimeout", "tenantIds")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WORKER_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    MAXJOBSTOACTIVATE_FIELD_NUMBER: _ClassVar[int]
    FETCHVARIABLE_FIELD_NUMBER: _ClassVar[int]
    REQUESTTIMEOUT_FIELD_NUMBER: _ClassVar[int]
    TENANTIDS_FIELD_NUMBER: _ClassVar[int]
    type: str
    worker: str
    timeout: int
    maxJobsToActivate: int
    fetchVariable: _containers.RepeatedScalarFieldContainer[str]
    requestTimeout: int
    tenantIds: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, type: _Optional[str] = ..., worker: _Optional[str] = ..., timeout: _Optional[int] = ..., maxJobsToActivate: _Optional[int] = ..., fetchVariable: _Optional[_Iterable[str]] = ..., requestTimeout: _Optional[int] = ..., tenantIds: _Optional[_Iterable[str]] = ...) -> None: ...

class ActivateJobsResponse(_message.Message):
    __slots__ = ("jobs",)
    JOBS_FIELD_NUMBER: _ClassVar[int]
    jobs: _containers.RepeatedCompositeFieldContainer[ActivatedJob]
    def __init__(self, jobs: _Optional[_Iterable[_Union[ActivatedJob, _Mapping]]] = ...) -> None: ...

class ActivatedJob(_message.Message):
    __slots__ = ("key", "type", "processInstanceKey", "bpmnProcessId", "processDefinitionVersion", "processDefinitionKey", "elementId", "elementInstanceKey", "customHeaders", "worker", "retries", "deadline", "variables", "tenantId")
    KEY_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PROCESSINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    BPMNPROCESSID_FIELD_NUMBER: _ClassVar[int]
    PROCESSDEFINITIONVERSION_FIELD_NUMBER: _ClassVar[int]
    PROCESSDEFINITIONKEY_FIELD_NUMBER: _ClassVar[int]
    ELEMENTID_FIELD_NUMBER: _ClassVar[int]
    ELEMENTINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    CUSTOMHEADERS_FIELD_NUMBER: _ClassVar[int]
    WORKER_FIELD_NUMBER: _ClassVar[int]
    RETRIES_FIELD_NUMBER: _ClassVar[int]
    DEADLINE_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    key: int
    type: str
    processInstanceKey: int
    bpmnProcessId: str
    processDefinitionVersion: int
    processDefinitionKey: int
    elementId: str
    elementInstanceKey: int
    customHeaders: str
    worker: str
    retries: int
    deadline: int
    variables: str
    tenantId: str
    def __init__(self, key: _Optional[int] = ..., type: _Optional[str] = ..., processInstanceKey: _Optional[int] = ..., bpmnProcessId: _Optional[str] = ..., processDefinitionVersion: _Optional[int] = ..., processDefinitionKey: _Optional[int] = ..., elementId: _Optional[str] = ..., elementInstanceKey: _Optional[int] = ..., customHeaders: _Optional[str] = ..., worker: _Optional[str] = ..., retries: _Optional[int] = ..., deadline: _Optional[int] = ..., variables: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class CancelProcessInstanceRequest(_message.Message):
    __slots__ = ("processInstanceKey", "operationReference")
    PROCESSINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    processInstanceKey: int
    operationReference: int
    def __init__(self, processInstanceKey: _Optional[int] = ..., operationReference: _Optional[int] = ...) -> None: ...

class CancelProcessInstanceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CompleteJobRequest(_message.Message):
    __slots__ = ("jobKey", "variables")
    JOBKEY_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    jobKey: int
    variables: str
    def __init__(self, jobKey: _Optional[int] = ..., variables: _Optional[str] = ...) -> None: ...

class CompleteJobResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CreateProcessInstanceRequest(_message.Message):
    __slots__ = ("processDefinitionKey", "bpmnProcessId", "version", "variables", "startInstructions", "tenantId", "operationReference")
    PROCESSDEFINITIONKEY_FIELD_NUMBER: _ClassVar[int]
    BPMNPROCESSID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    STARTINSTRUCTIONS_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    processDefinitionKey: int
    bpmnProcessId: str
    version: int
    variables: str
    startInstructions: _containers.RepeatedCompositeFieldContainer[ProcessInstanceCreationStartInstruction]
    tenantId: str
    operationReference: int
    def __init__(self, processDefinitionKey: _Optional[int] = ..., bpmnProcessId: _Optional[str] = ..., version: _Optional[int] = ..., variables: _Optional[str] = ..., startInstructions: _Optional[_Iterable[_Union[ProcessInstanceCreationStartInstruction, _Mapping]]] = ..., tenantId: _Optional[str] = ..., operationReference: _Optional[int] = ...) -> None: ...

class ProcessInstanceCreationStartInstruction(_message.Message):
    __slots__ = ("elementId",)
    ELEMENTID_FIELD_NUMBER: _ClassVar[int]
    elementId: str
    def __init__(self, elementId: _Optional[str] = ...) -> None: ...

class CreateProcessInstanceResponse(_message.Message):
    __slots__ = ("processDefinitionKey", "bpmnProcessId", "version", "processInstanceKey", "tenantId")
    PROCESSDEFINITIONKEY_FIELD_NUMBER: _ClassVar[int]
    BPMNPROCESSID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PROCESSINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    processDefinitionKey: int
    bpmnProcessId: str
    version: int
    processInstanceKey: int
    tenantId: str
    def __init__(self, processDefinitionKey: _Optional[int] = ..., bpmnProcessId: _Optional[str] = ..., version: _Optional[int] = ..., processInstanceKey: _Optional[int] = ..., tenantId: _Optional[str] = ...) -> None: ...

class CreateProcessInstanceWithResultRequest(_message.Message):
    __slots__ = ("request", "requestTimeout", "fetchVariables")
    REQUEST_FIELD_NUMBER: _ClassVar[int]
    REQUESTTIMEOUT_FIELD_NUMBER: _ClassVar[int]
    FETCHVARIABLES_FIELD_NUMBER: _ClassVar[int]
    request: CreateProcessInstanceRequest
    requestTimeout: int
    fetchVariables: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, request: _Optional[_Union[CreateProcessInstanceRequest, _Mapping]] = ..., requestTimeout: _Optional[int] = ..., fetchVariables: _Optional[_Iterable[str]] = ...) -> None: ...

class CreateProcessInstanceWithResultResponse(_message.Message):
    __slots__ = ("processDefinitionKey", "bpmnProcessId", "version", "processInstanceKey", "variables", "tenantId")
    PROCESSDEFINITIONKEY_FIELD_NUMBER: _ClassVar[int]
    BPMNPROCESSID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PROCESSINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    processDefinitionKey: int
    bpmnProcessId: str
    version: int
    processInstanceKey: int
    variables: str
    tenantId: str
    def __init__(self, processDefinitionKey: _Optional[int] = ..., bpmnProcessId: _Optional[str] = ..., version: _Optional[int] = ..., processInstanceKey: _Optional[int] = ..., variables: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class EvaluateDecisionRequest(_message.Message):
    __slots__ = ("decisionKey", "decisionId", "variables", "tenantId")
    DECISIONKEY_FIELD_NUMBER: _ClassVar[int]
    DECISIONID_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    decisionKey: int
    decisionId: str
    variables: str
    tenantId: str
    def __init__(self, decisionKey: _Optional[int] = ..., decisionId: _Optional[str] = ..., variables: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class EvaluateDecisionResponse(_message.Message):
    __slots__ = ("decisionKey", "decisionId", "decisionName", "decisionVersion", "decisionRequirementsId", "decisionRequirementsKey", "decisionOutput", "evaluatedDecisions", "failedDecisionId", "failureMessage", "tenantId", "decisionInstanceKey")
    DECISIONKEY_FIELD_NUMBER: _ClassVar[int]
    DECISIONID_FIELD_NUMBER: _ClassVar[int]
    DECISIONNAME_FIELD_NUMBER: _ClassVar[int]
    DECISIONVERSION_FIELD_NUMBER: _ClassVar[int]
    DECISIONREQUIREMENTSID_FIELD_NUMBER: _ClassVar[int]
    DECISIONREQUIREMENTSKEY_FIELD_NUMBER: _ClassVar[int]
    DECISIONOUTPUT_FIELD_NUMBER: _ClassVar[int]
    EVALUATEDDECISIONS_FIELD_NUMBER: _ClassVar[int]
    FAILEDDECISIONID_FIELD_NUMBER: _ClassVar[int]
    FAILUREMESSAGE_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    DECISIONINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    decisionKey: int
    decisionId: str
    decisionName: str
    decisionVersion: int
    decisionRequirementsId: str
    decisionRequirementsKey: int
    decisionOutput: str
    evaluatedDecisions: _containers.RepeatedCompositeFieldContainer[EvaluatedDecision]
    failedDecisionId: str
    failureMessage: str
    tenantId: str
    decisionInstanceKey: int
    def __init__(self, decisionKey: _Optional[int] = ..., decisionId: _Optional[str] = ..., decisionName: _Optional[str] = ..., decisionVersion: _Optional[int] = ..., decisionRequirementsId: _Optional[str] = ..., decisionRequirementsKey: _Optional[int] = ..., decisionOutput: _Optional[str] = ..., evaluatedDecisions: _Optional[_Iterable[_Union[EvaluatedDecision, _Mapping]]] = ..., failedDecisionId: _Optional[str] = ..., failureMessage: _Optional[str] = ..., tenantId: _Optional[str] = ..., decisionInstanceKey: _Optional[int] = ...) -> None: ...

class EvaluatedDecision(_message.Message):
    __slots__ = ("decisionKey", "decisionId", "decisionName", "decisionVersion", "decisionType", "decisionOutput", "matchedRules", "evaluatedInputs", "tenantId")
    DECISIONKEY_FIELD_NUMBER: _ClassVar[int]
    DECISIONID_FIELD_NUMBER: _ClassVar[int]
    DECISIONNAME_FIELD_NUMBER: _ClassVar[int]
    DECISIONVERSION_FIELD_NUMBER: _ClassVar[int]
    DECISIONTYPE_FIELD_NUMBER: _ClassVar[int]
    DECISIONOUTPUT_FIELD_NUMBER: _ClassVar[int]
    MATCHEDRULES_FIELD_NUMBER: _ClassVar[int]
    EVALUATEDINPUTS_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    decisionKey: int
    decisionId: str
    decisionName: str
    decisionVersion: int
    decisionType: str
    decisionOutput: str
    matchedRules: _containers.RepeatedCompositeFieldContainer[MatchedDecisionRule]
    evaluatedInputs: _containers.RepeatedCompositeFieldContainer[EvaluatedDecisionInput]
    tenantId: str
    def __init__(self, decisionKey: _Optional[int] = ..., decisionId: _Optional[str] = ..., decisionName: _Optional[str] = ..., decisionVersion: _Optional[int] = ..., decisionType: _Optional[str] = ..., decisionOutput: _Optional[str] = ..., matchedRules: _Optional[_Iterable[_Union[MatchedDecisionRule, _Mapping]]] = ..., evaluatedInputs: _Optional[_Iterable[_Union[EvaluatedDecisionInput, _Mapping]]] = ..., tenantId: _Optional[str] = ...) -> None: ...

class EvaluatedDecisionInput(_message.Message):
    __slots__ = ("inputId", "inputName", "inputValue")
    INPUTID_FIELD_NUMBER: _ClassVar[int]
    INPUTNAME_FIELD_NUMBER: _ClassVar[int]
    INPUTVALUE_FIELD_NUMBER: _ClassVar[int]
    inputId: str
    inputName: str
    inputValue: str
    def __init__(self, inputId: _Optional[str] = ..., inputName: _Optional[str] = ..., inputValue: _Optional[str] = ...) -> None: ...

class EvaluatedDecisionOutput(_message.Message):
    __slots__ = ("outputId", "outputName", "outputValue")
    OUTPUTID_FIELD_NUMBER: _ClassVar[int]
    OUTPUTNAME_FIELD_NUMBER: _ClassVar[int]
    OUTPUTVALUE_FIELD_NUMBER: _ClassVar[int]
    outputId: str
    outputName: str
    outputValue: str
    def __init__(self, outputId: _Optional[str] = ..., outputName: _Optional[str] = ..., outputValue: _Optional[str] = ...) -> None: ...

class MatchedDecisionRule(_message.Message):
    __slots__ = ("ruleId", "ruleIndex", "evaluatedOutputs")
    RULEID_FIELD_NUMBER: _ClassVar[int]
    RULEINDEX_FIELD_NUMBER: _ClassVar[int]
    EVALUATEDOUTPUTS_FIELD_NUMBER: _ClassVar[int]
    ruleId: str
    ruleIndex: int
    evaluatedOutputs: _containers.RepeatedCompositeFieldContainer[EvaluatedDecisionOutput]
    def __init__(self, ruleId: _Optional[str] = ..., ruleIndex: _Optional[int] = ..., evaluatedOutputs: _Optional[_Iterable[_Union[EvaluatedDecisionOutput, _Mapping]]] = ...) -> None: ...

class DeployProcessRequest(_message.Message):
    __slots__ = ("processes",)
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    processes: _containers.RepeatedCompositeFieldContainer[ProcessRequestObject]
    def __init__(self, processes: _Optional[_Iterable[_Union[ProcessRequestObject, _Mapping]]] = ...) -> None: ...

class ProcessRequestObject(_message.Message):
    __slots__ = ("name", "definition")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    name: str
    definition: bytes
    def __init__(self, name: _Optional[str] = ..., definition: _Optional[bytes] = ...) -> None: ...

class DeployProcessResponse(_message.Message):
    __slots__ = ("key", "processes")
    KEY_FIELD_NUMBER: _ClassVar[int]
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    key: int
    processes: _containers.RepeatedCompositeFieldContainer[ProcessMetadata]
    def __init__(self, key: _Optional[int] = ..., processes: _Optional[_Iterable[_Union[ProcessMetadata, _Mapping]]] = ...) -> None: ...

class DeployResourceRequest(_message.Message):
    __slots__ = ("resources", "tenantId")
    RESOURCES_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    resources: _containers.RepeatedCompositeFieldContainer[Resource]
    tenantId: str
    def __init__(self, resources: _Optional[_Iterable[_Union[Resource, _Mapping]]] = ..., tenantId: _Optional[str] = ...) -> None: ...

class Resource(_message.Message):
    __slots__ = ("name", "content")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    name: str
    content: bytes
    def __init__(self, name: _Optional[str] = ..., content: _Optional[bytes] = ...) -> None: ...

class DeployResourceResponse(_message.Message):
    __slots__ = ("key", "deployments", "tenantId")
    KEY_FIELD_NUMBER: _ClassVar[int]
    DEPLOYMENTS_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    key: int
    deployments: _containers.RepeatedCompositeFieldContainer[Deployment]
    tenantId: str
    def __init__(self, key: _Optional[int] = ..., deployments: _Optional[_Iterable[_Union[Deployment, _Mapping]]] = ..., tenantId: _Optional[str] = ...) -> None: ...

class Deployment(_message.Message):
    __slots__ = ("process", "decision", "decisionRequirements", "form")
    PROCESS_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    DECISIONREQUIREMENTS_FIELD_NUMBER: _ClassVar[int]
    FORM_FIELD_NUMBER: _ClassVar[int]
    process: ProcessMetadata
    decision: DecisionMetadata
    decisionRequirements: DecisionRequirementsMetadata
    form: FormMetadata
    def __init__(self, process: _Optional[_Union[ProcessMetadata, _Mapping]] = ..., decision: _Optional[_Union[DecisionMetadata, _Mapping]] = ..., decisionRequirements: _Optional[_Union[DecisionRequirementsMetadata, _Mapping]] = ..., form: _Optional[_Union[FormMetadata, _Mapping]] = ...) -> None: ...

class ProcessMetadata(_message.Message):
    __slots__ = ("bpmnProcessId", "version", "processDefinitionKey", "resourceName", "tenantId")
    BPMNPROCESSID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PROCESSDEFINITIONKEY_FIELD_NUMBER: _ClassVar[int]
    RESOURCENAME_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    bpmnProcessId: str
    version: int
    processDefinitionKey: int
    resourceName: str
    tenantId: str
    def __init__(self, bpmnProcessId: _Optional[str] = ..., version: _Optional[int] = ..., processDefinitionKey: _Optional[int] = ..., resourceName: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class DecisionMetadata(_message.Message):
    __slots__ = ("dmnDecisionId", "dmnDecisionName", "version", "decisionKey", "dmnDecisionRequirementsId", "decisionRequirementsKey", "tenantId")
    DMNDECISIONID_FIELD_NUMBER: _ClassVar[int]
    DMNDECISIONNAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DECISIONKEY_FIELD_NUMBER: _ClassVar[int]
    DMNDECISIONREQUIREMENTSID_FIELD_NUMBER: _ClassVar[int]
    DECISIONREQUIREMENTSKEY_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    dmnDecisionId: str
    dmnDecisionName: str
    version: int
    decisionKey: int
    dmnDecisionRequirementsId: str
    decisionRequirementsKey: int
    tenantId: str
    def __init__(self, dmnDecisionId: _Optional[str] = ..., dmnDecisionName: _Optional[str] = ..., version: _Optional[int] = ..., decisionKey: _Optional[int] = ..., dmnDecisionRequirementsId: _Optional[str] = ..., decisionRequirementsKey: _Optional[int] = ..., tenantId: _Optional[str] = ...) -> None: ...

class DecisionRequirementsMetadata(_message.Message):
    __slots__ = ("dmnDecisionRequirementsId", "dmnDecisionRequirementsName", "version", "decisionRequirementsKey", "resourceName", "tenantId")
    DMNDECISIONREQUIREMENTSID_FIELD_NUMBER: _ClassVar[int]
    DMNDECISIONREQUIREMENTSNAME_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    DECISIONREQUIREMENTSKEY_FIELD_NUMBER: _ClassVar[int]
    RESOURCENAME_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    dmnDecisionRequirementsId: str
    dmnDecisionRequirementsName: str
    version: int
    decisionRequirementsKey: int
    resourceName: str
    tenantId: str
    def __init__(self, dmnDecisionRequirementsId: _Optional[str] = ..., dmnDecisionRequirementsName: _Optional[str] = ..., version: _Optional[int] = ..., decisionRequirementsKey: _Optional[int] = ..., resourceName: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class FormMetadata(_message.Message):
    __slots__ = ("formId", "version", "formKey", "resourceName", "tenantId")
    FORMID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    FORMKEY_FIELD_NUMBER: _ClassVar[int]
    RESOURCENAME_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    formId: str
    version: int
    formKey: int
    resourceName: str
    tenantId: str
    def __init__(self, formId: _Optional[str] = ..., version: _Optional[int] = ..., formKey: _Optional[int] = ..., resourceName: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class FailJobRequest(_message.Message):
    __slots__ = ("jobKey", "retries", "errorMessage", "retryBackOff", "variables")
    JOBKEY_FIELD_NUMBER: _ClassVar[int]
    RETRIES_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    RETRYBACKOFF_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    jobKey: int
    retries: int
    errorMessage: str
    retryBackOff: int
    variables: str
    def __init__(self, jobKey: _Optional[int] = ..., retries: _Optional[int] = ..., errorMessage: _Optional[str] = ..., retryBackOff: _Optional[int] = ..., variables: _Optional[str] = ...) -> None: ...

class FailJobResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ThrowErrorRequest(_message.Message):
    __slots__ = ("jobKey", "errorCode", "errorMessage", "variables")
    JOBKEY_FIELD_NUMBER: _ClassVar[int]
    ERRORCODE_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    jobKey: int
    errorCode: str
    errorMessage: str
    variables: str
    def __init__(self, jobKey: _Optional[int] = ..., errorCode: _Optional[str] = ..., errorMessage: _Optional[str] = ..., variables: _Optional[str] = ...) -> None: ...

class ThrowErrorResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PublishMessageRequest(_message.Message):
    __slots__ = ("name", "correlationKey", "timeToLive", "messageId", "variables", "tenantId")
    NAME_FIELD_NUMBER: _ClassVar[int]
    CORRELATIONKEY_FIELD_NUMBER: _ClassVar[int]
    TIMETOLIVE_FIELD_NUMBER: _ClassVar[int]
    MESSAGEID_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    name: str
    correlationKey: str
    timeToLive: int
    messageId: str
    variables: str
    tenantId: str
    def __init__(self, name: _Optional[str] = ..., correlationKey: _Optional[str] = ..., timeToLive: _Optional[int] = ..., messageId: _Optional[str] = ..., variables: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class PublishMessageResponse(_message.Message):
    __slots__ = ("key", "tenantId")
    KEY_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    key: int
    tenantId: str
    def __init__(self, key: _Optional[int] = ..., tenantId: _Optional[str] = ...) -> None: ...

class ResolveIncidentRequest(_message.Message):
    __slots__ = ("incidentKey", "operationReference")
    INCIDENTKEY_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    incidentKey: int
    operationReference: int
    def __init__(self, incidentKey: _Optional[int] = ..., operationReference: _Optional[int] = ...) -> None: ...

class ResolveIncidentResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TopologyRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class TopologyResponse(_message.Message):
    __slots__ = ("brokers", "clusterSize", "partitionsCount", "replicationFactor", "gatewayVersion")
    BROKERS_FIELD_NUMBER: _ClassVar[int]
    CLUSTERSIZE_FIELD_NUMBER: _ClassVar[int]
    PARTITIONSCOUNT_FIELD_NUMBER: _ClassVar[int]
    REPLICATIONFACTOR_FIELD_NUMBER: _ClassVar[int]
    GATEWAYVERSION_FIELD_NUMBER: _ClassVar[int]
    brokers: _containers.RepeatedCompositeFieldContainer[BrokerInfo]
    clusterSize: int
    partitionsCount: int
    replicationFactor: int
    gatewayVersion: str
    def __init__(self, brokers: _Optional[_Iterable[_Union[BrokerInfo, _Mapping]]] = ..., clusterSize: _Optional[int] = ..., partitionsCount: _Optional[int] = ..., replicationFactor: _Optional[int] = ..., gatewayVersion: _Optional[str] = ...) -> None: ...

class BrokerInfo(_message.Message):
    __slots__ = ("nodeId", "host", "port", "partitions", "version")
    NODEID_FIELD_NUMBER: _ClassVar[int]
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    PARTITIONS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    nodeId: int
    host: str
    port: int
    partitions: _containers.RepeatedCompositeFieldContainer[Partition]
    version: str
    def __init__(self, nodeId: _Optional[int] = ..., host: _Optional[str] = ..., port: _Optional[int] = ..., partitions: _Optional[_Iterable[_Union[Partition, _Mapping]]] = ..., version: _Optional[str] = ...) -> None: ...

class Partition(_message.Message):
    __slots__ = ("partitionId", "role", "health")
    class PartitionBrokerRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LEADER: _ClassVar[Partition.PartitionBrokerRole]
        FOLLOWER: _ClassVar[Partition.PartitionBrokerRole]
        INACTIVE: _ClassVar[Partition.PartitionBrokerRole]
    LEADER: Partition.PartitionBrokerRole
    FOLLOWER: Partition.PartitionBrokerRole
    INACTIVE: Partition.PartitionBrokerRole
    class PartitionBrokerHealth(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        HEALTHY: _ClassVar[Partition.PartitionBrokerHealth]
        UNHEALTHY: _ClassVar[Partition.PartitionBrokerHealth]
        DEAD: _ClassVar[Partition.PartitionBrokerHealth]
    HEALTHY: Partition.PartitionBrokerHealth
    UNHEALTHY: Partition.PartitionBrokerHealth
    DEAD: Partition.PartitionBrokerHealth
    PARTITIONID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    HEALTH_FIELD_NUMBER: _ClassVar[int]
    partitionId: int
    role: Partition.PartitionBrokerRole
    health: Partition.PartitionBrokerHealth
    def __init__(self, partitionId: _Optional[int] = ..., role: _Optional[_Union[Partition.PartitionBrokerRole, str]] = ..., health: _Optional[_Union[Partition.PartitionBrokerHealth, str]] = ...) -> None: ...

class UpdateJobRetriesRequest(_message.Message):
    __slots__ = ("jobKey", "retries", "operationReference")
    JOBKEY_FIELD_NUMBER: _ClassVar[int]
    RETRIES_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    jobKey: int
    retries: int
    operationReference: int
    def __init__(self, jobKey: _Optional[int] = ..., retries: _Optional[int] = ..., operationReference: _Optional[int] = ...) -> None: ...

class UpdateJobRetriesResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UpdateJobTimeoutRequest(_message.Message):
    __slots__ = ("jobKey", "timeout", "operationReference")
    JOBKEY_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    jobKey: int
    timeout: int
    operationReference: int
    def __init__(self, jobKey: _Optional[int] = ..., timeout: _Optional[int] = ..., operationReference: _Optional[int] = ...) -> None: ...

class UpdateJobTimeoutResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetVariablesRequest(_message.Message):
    __slots__ = ("elementInstanceKey", "variables", "local", "operationReference")
    ELEMENTINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    LOCAL_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    elementInstanceKey: int
    variables: str
    local: bool
    operationReference: int
    def __init__(self, elementInstanceKey: _Optional[int] = ..., variables: _Optional[str] = ..., local: bool = ..., operationReference: _Optional[int] = ...) -> None: ...

class SetVariablesResponse(_message.Message):
    __slots__ = ("key",)
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: int
    def __init__(self, key: _Optional[int] = ...) -> None: ...

class ModifyProcessInstanceRequest(_message.Message):
    __slots__ = ("processInstanceKey", "activateInstructions", "terminateInstructions", "operationReference")
    class ActivateInstruction(_message.Message):
        __slots__ = ("elementId", "ancestorElementInstanceKey", "variableInstructions")
        ELEMENTID_FIELD_NUMBER: _ClassVar[int]
        ANCESTORELEMENTINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
        VARIABLEINSTRUCTIONS_FIELD_NUMBER: _ClassVar[int]
        elementId: str
        ancestorElementInstanceKey: int
        variableInstructions: _containers.RepeatedCompositeFieldContainer[ModifyProcessInstanceRequest.VariableInstruction]
        def __init__(self, elementId: _Optional[str] = ..., ancestorElementInstanceKey: _Optional[int] = ..., variableInstructions: _Optional[_Iterable[_Union[ModifyProcessInstanceRequest.VariableInstruction, _Mapping]]] = ...) -> None: ...
    class VariableInstruction(_message.Message):
        __slots__ = ("variables", "scopeId")
        VARIABLES_FIELD_NUMBER: _ClassVar[int]
        SCOPEID_FIELD_NUMBER: _ClassVar[int]
        variables: str
        scopeId: str
        def __init__(self, variables: _Optional[str] = ..., scopeId: _Optional[str] = ...) -> None: ...
    class TerminateInstruction(_message.Message):
        __slots__ = ("elementInstanceKey",)
        ELEMENTINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
        elementInstanceKey: int
        def __init__(self, elementInstanceKey: _Optional[int] = ...) -> None: ...
    PROCESSINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    ACTIVATEINSTRUCTIONS_FIELD_NUMBER: _ClassVar[int]
    TERMINATEINSTRUCTIONS_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    processInstanceKey: int
    activateInstructions: _containers.RepeatedCompositeFieldContainer[ModifyProcessInstanceRequest.ActivateInstruction]
    terminateInstructions: _containers.RepeatedCompositeFieldContainer[ModifyProcessInstanceRequest.TerminateInstruction]
    operationReference: int
    def __init__(self, processInstanceKey: _Optional[int] = ..., activateInstructions: _Optional[_Iterable[_Union[ModifyProcessInstanceRequest.ActivateInstruction, _Mapping]]] = ..., terminateInstructions: _Optional[_Iterable[_Union[ModifyProcessInstanceRequest.TerminateInstruction, _Mapping]]] = ..., operationReference: _Optional[int] = ...) -> None: ...

class ModifyProcessInstanceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MigrateProcessInstanceRequest(_message.Message):
    __slots__ = ("processInstanceKey", "migrationPlan", "operationReference")
    class MigrationPlan(_message.Message):
        __slots__ = ("targetProcessDefinitionKey", "mappingInstructions")
        TARGETPROCESSDEFINITIONKEY_FIELD_NUMBER: _ClassVar[int]
        MAPPINGINSTRUCTIONS_FIELD_NUMBER: _ClassVar[int]
        targetProcessDefinitionKey: int
        mappingInstructions: _containers.RepeatedCompositeFieldContainer[MigrateProcessInstanceRequest.MappingInstruction]
        def __init__(self, targetProcessDefinitionKey: _Optional[int] = ..., mappingInstructions: _Optional[_Iterable[_Union[MigrateProcessInstanceRequest.MappingInstruction, _Mapping]]] = ...) -> None: ...
    class MappingInstruction(_message.Message):
        __slots__ = ("sourceElementId", "targetElementId")
        SOURCEELEMENTID_FIELD_NUMBER: _ClassVar[int]
        TARGETELEMENTID_FIELD_NUMBER: _ClassVar[int]
        sourceElementId: str
        targetElementId: str
        def __init__(self, sourceElementId: _Optional[str] = ..., targetElementId: _Optional[str] = ...) -> None: ...
    PROCESSINSTANCEKEY_FIELD_NUMBER: _ClassVar[int]
    MIGRATIONPLAN_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    processInstanceKey: int
    migrationPlan: MigrateProcessInstanceRequest.MigrationPlan
    operationReference: int
    def __init__(self, processInstanceKey: _Optional[int] = ..., migrationPlan: _Optional[_Union[MigrateProcessInstanceRequest.MigrationPlan, _Mapping]] = ..., operationReference: _Optional[int] = ...) -> None: ...

class MigrateProcessInstanceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class DeleteResourceRequest(_message.Message):
    __slots__ = ("resourceKey", "operationReference")
    RESOURCEKEY_FIELD_NUMBER: _ClassVar[int]
    OPERATIONREFERENCE_FIELD_NUMBER: _ClassVar[int]
    resourceKey: int
    operationReference: int
    def __init__(self, resourceKey: _Optional[int] = ..., operationReference: _Optional[int] = ...) -> None: ...

class DeleteResourceResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class BroadcastSignalRequest(_message.Message):
    __slots__ = ("signalName", "variables", "tenantId")
    SIGNALNAME_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    signalName: str
    variables: str
    tenantId: str
    def __init__(self, signalName: _Optional[str] = ..., variables: _Optional[str] = ..., tenantId: _Optional[str] = ...) -> None: ...

class BroadcastSignalResponse(_message.Message):
    __slots__ = ("key", "tenantId")
    KEY_FIELD_NUMBER: _ClassVar[int]
    TENANTID_FIELD_NUMBER: _ClassVar[int]
    key: int
    tenantId: str
    def __init__(self, key: _Optional[int] = ..., tenantId: _Optional[str] = ...) -> None: ...
