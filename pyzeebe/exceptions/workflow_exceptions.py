from pyzeebe.exceptions.pyzeebe_exceptions import PyZeebeException


class WorkflowNotFound(PyZeebeException):
    def __init__(self, bpmn_process_id: str, version: int):
        super().__init__(
            f"Workflow definition: {bpmn_process_id}  with {version} was not found")
        self.bpmn_process_id = bpmn_process_id
        self.version = version


class WorkflowInstanceNotFound(PyZeebeException):
    def __init__(self, workflow_instance_key: int):
        super().__init__(f"Workflow instance key: {workflow_instance_key} was not found")
        self.workflow_instance_key = workflow_instance_key


class WorkflowHasNoStartEvent(PyZeebeException):
    def __init__(self, bpmn_process_id: str):
        super().__init__(f"Workflow {bpmn_process_id} has no start event that can be called manually")
        self.bpmn_process_id = bpmn_process_id


class WorkflowInvalid(PyZeebeException):
    pass


class InvalidJSON(PyZeebeException):
    pass
