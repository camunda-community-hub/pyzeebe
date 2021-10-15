from pyzeebe.errors.pyzeebe_errors import PyZeebeError


class ProcessDefinitionNotFoundError(PyZeebeError):
    def __init__(self, bpmn_process_id: str, version: int):
        super().__init__(
            f"Process definition: {bpmn_process_id}  with {version} was not found"
        )
        self.bpmn_process_id = bpmn_process_id
        self.version = version


class ProcessInstanceNotFoundError(PyZeebeError):
    def __init__(self, process_instance_key: int):
        super().__init__(f"Process instance key: {process_instance_key} was not found")
        self.process_instance_key = process_instance_key


class ProcessDefinitionHasNoStartEventError(PyZeebeError):
    def __init__(self, bpmn_process_id: str):
        super().__init__(
            f"Process {bpmn_process_id} has no start event that can be called manually"
        )
        self.bpmn_process_id = bpmn_process_id


class ProcessInvalidError(PyZeebeError):
    pass


class InvalidJSONError(PyZeebeError):
    pass


class ProcessTimeoutError(PyZeebeError, TimeoutError):
    def __init__(self, bpmn_process_id: str):
        super().__init__(
            f"Timeout while waiting for process {bpmn_process_id} to complete"
        )
        self.bpmn_process_id = bpmn_process_id
