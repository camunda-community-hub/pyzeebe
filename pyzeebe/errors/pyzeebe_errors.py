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
