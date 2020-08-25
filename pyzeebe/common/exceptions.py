class TaskNotFound(Exception):
    pass


class WorkflowNotFound(Exception):
    def __init__(self, bpmn_process_id: str, version: int):
        super().__init__(
            f'Workflow definition: {bpmn_process_id}  with {version} was not found')
        self.bpmn_process_id = bpmn_process_id
        self.version = version


class WorkflowInstanceNotFound(Exception):
    """
    GRPC_STATUS_NOT_FOUND
    Returned if:
        no workflow with the given key exists (if workflowKey was given)
        no workflow with the given process ID exists (if bpmnProcessId was given but version was -1)
        no workflow with the given process ID and version exists (if both bpmnProcessId and version were given)

    GRPC_STATUS_INVALID_ARGUMENT
    Returned if:
        the given variables argument is not a valid JSON document; it is expected to be a valid JSON document where the root node is an object.

    """

    def __init__(self, workflow_instance_key: int):
        super().__init__(f'Workflow instance key: {workflow_instance_key} was not found')
        self.workflow_instance_key = workflow_instance_key


class WorkflowHasNoStartEvent(Exception):
    """
    GRPC_STATUS_FAILED_PRECONDITION
    Returned if:
        the workflow definition does not contain a none start event; only workflows with none start event can be started manually.
    """
    pass


class InvalidActivateJobs(Exception):
    """
    GRPC_STATUS_INVALID_ARGUMENT
    Returned if:
        type is blank (empty string, null)
        worker is blank (empty string, null)
        timeout less than 1 (ms)
        amount is less than 1
    """
    pass


class InvalidCompleteJob(Exception):
    """
    GRPC_STATUS_NOT_FOUND
    Returned if:
        no job exists with the given job key. Note that since jobs are removed once completed, it could be that this job did exist at some point.

    GRPC_STATUS_FAILED_PRECONDITION
    Returned if:
        the job was marked as failed. In that case, the related incident must be resolved before the job can be activated again and completed.
    """
    pass


class JobAlreadyFailed(Exception):
    pass


class JobNotFound(Exception):
    pass


class InvalidFailJob(Exception):
    """
    GRPC_STATUS_NOT_FOUND
    Returned if:
        no job was found with the given key

    GRPC_STATUS_FAILED_PRECONDITION
    Returned if:
        the job was not activated
        the job is already in a failed state, i.e. ran out of retries
    """
    pass


class InvalidDeployWorkflow(Exception):
    """
    GRPC_STATUS_INVALID_ARGUMENT
    Returned if:
        no resources given.
        if at least one resource is invalid. A resource is considered invalid if:
        it is not a BPMN or YAML file (currently detected through the file extension)
        the resource data is not deserializable (e.g. detected as BPMN, but it's broken XML)
        the workflow is invalid (e.g. an event-based gateway has an outgoing sequence flow to a task)
    """
    pass


class MessageAlreadyExists(Exception):
    """
    GRPC_STATUS_ALREADY_EXISTS
    Returned if:
        a message with the same ID was previously published (and is still alive)
    """
    pass


class IncidentNotFound(Exception):
    """
    GRPC_STATUS_NOT_FOUND
    Returned if:
        no incident with the given key exists
    """
    pass


class ElementNotFound(Exception):
    pass


class InvalidJSON(Exception):
    pass


class InvalidSetVariables(Exception):
    """
    GRPC_STATUS_NOT_FOUND
    Returned if:
        no element with the given elementInstanceKey was exists

    GRPC_STATUS_INVALID_ARGUMENT
    Returned if:
        the given payload is not a valid JSON document; all payloads are expected to be valid JSON documents where the root node is an object.
    """
    pass


class InvalidThrowError(Exception):
    """
    Errors
    GRPC_STATUS_NOT_FOUND
    Returned if:
        no job was found with the given key

    GRPC_STATUS_FAILED_PRECONDITION
    Returned if:
        the job is already in a failed state, i.e. ran out of retries
    """
    pass


class InvalidJobRetries(Exception):
    """
    Errors
    GRPC_STATUS_NOT_FOUND
    Returned if:
        no job exists with the given key

    GRPC_STATUS_INVALID_ARGUMENT
    Returned if:
        retries is not greater than 0
    """
    pass


class ZeebeBackPressure(Exception):
    # TODO: Think about deploying some kind of retry strategy instead of raising this
    pass


class ZeebeGatewayUnavailable(Exception):
    pass


class ZeebeInternalError(Exception):
    pass
