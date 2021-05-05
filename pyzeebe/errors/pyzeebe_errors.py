class PyZeebeError(Exception):
    pass


class TaskNotFoundError(PyZeebeError):
    pass


class NoVariableNameGivenError(PyZeebeError):
    def __init__(self, task_type: str):
        super().__init__(f"No variable name given for single_value task {task_type}")
        self.task_type = task_type


class NoZeebeAdapterError(PyZeebeError):
    pass


class DuplicateTaskTypeError(PyZeebeError):
    def __init__(self, task_type: str):
        super().__init__(f"Task with type {task_type} already exists")
        self.task_type = task_type


class MaxConsecutiveTaskThreadError(PyZeebeError):
    pass


class BusinessException(PyZeebeException):
    """
    Exception that can be raised with a user defined code,
    to be caught later by an error event in the workflow
    """
    def __init__(self, error_code: str) -> None:
        super().__init__(f"Business error with code {error_code}")
        self.error_code = error_code

    def __repr__(self) -> str:
        return str({"error_code": self.error_code})