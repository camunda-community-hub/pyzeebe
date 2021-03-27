from pyzeebe.errors.pyzeebe_errors import PyZeebeError


class WorkflowNotFoundError(PyZeebeError):
    def __init__(self, bpmn_process_id: str, version: int):
        super().__init__(
            f"Workflow definition: {bpmn_process_id}  with {version} was not found")
        self.bpmn_process_id = bpmn_process_id
        self.version = version


class WorkflowInstanceNotFoundError(PyZeebeError):
    def __init__(self, workflow_instance_key: int):
        super().__init__(f"Workflow instance key: {workflow_instance_key} was not found")
        self.workflow_instance_key = workflow_instance_key


class WorkflowHasNoStartEventError(PyZeebeError):
    def __init__(self, bpmn_process_id: str):
        super().__init__(f"Workflow {bpmn_process_id} has no start event that can be called manually")
        self.bpmn_process_id = bpmn_process_id


class WorkflowInvalidError(PyZeebeError):
    pass


class InvalidJSONError(PyZeebeError):
    pass
