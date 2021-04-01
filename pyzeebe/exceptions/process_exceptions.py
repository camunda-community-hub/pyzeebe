from pyzeebe.exceptions.pyzeebe_exceptions import PyZeebeException


class ProcessNotFound(PyZeebeException):
    def __init__(self, bpmn_process_id: str, version: int):
        super().__init__(
            f"Process definition: {bpmn_process_id}  with {version} was not found")
        self.bpmn_process_id = bpmn_process_id
        self.version = version


class ProcessInstanceNotFound(PyZeebeException):
    def __init__(self, process_instance_key: int):
        super().__init__(
            f"Process instance key: {process_instance_key} was not found")
        self.process_instance_key = process_instance_key


class ProcessHasNoStartEvent(PyZeebeException):
    def __init__(self, bpmn_process_id: str):
        super().__init__(
            f"Process {bpmn_process_id} has no start event that can be called manually")
        self.bpmn_process_id = bpmn_process_id


class ProcessInvalid(PyZeebeException):
    pass


class InvalidJSON(PyZeebeException):
    pass
