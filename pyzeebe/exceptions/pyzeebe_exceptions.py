class PyZeebeException(Exception):
    pass


class TaskNotFound(PyZeebeException):
    pass


class NoVariableNameGiven(PyZeebeException):
    def __init__(self, task_type: str):
        super().__init__(f"No variable name given for single_value task {task_type}")
        self.task_type = task_type


class NoZeebeAdapter(PyZeebeException):
    pass
