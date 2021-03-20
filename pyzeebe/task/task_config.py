from typing import List

from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.types import TaskDecorator


class TaskConfig:
    def __init__(self, type: str, exception_handler: ExceptionHandler,
                 timeout_ms: int, max_jobs_to_activate: int,
                 variables_to_fetch: List[str],
                 single_value: bool, variable_name: str, before: List[TaskDecorator],
                 after: List[TaskDecorator]):
        self.type = type
        self.exception_handler = exception_handler
        self.timeout_ms = timeout_ms
        self.max_jobs_to_activate = max_jobs_to_activate
        self.variables_to_fetch = variables_to_fetch
        self.single_value = single_value
        self.variable_name = variable_name
        self.before = before
        self.after = after

    def __repr__(self):
        return f"TaskConfig(type={self.type}, exception_handler={self.exception_handler}, " \
               f"timeout_ms={self.timeout_ms}, max_jobs_to_activate={self.max_jobs_to_activate}, " \
               f"variables_to_fetch={self.variables_to_fetch}, single_value={self.single_value}, " \
               f"variable_name={self.variable_name}, before={self.before}, after={self.after})"
