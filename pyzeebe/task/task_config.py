from typing import List, Optional

from pyzeebe.errors import NoVariableNameGivenError
from pyzeebe.function_tools import async_tools
from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.types import AsyncTaskDecorator, TaskDecorator


class TaskConfig:
    before: List[AsyncTaskDecorator]
    after: List[AsyncTaskDecorator]

    def __init__(self, type: str, exception_handler: ExceptionHandler,
                 timeout_ms: int, max_jobs_to_activate: int, max_running_jobs: int,
                 variables_to_fetch: List[str],
                 single_value: bool, variable_name: str, before: List[TaskDecorator],
                 after: List[TaskDecorator]):
        if single_value and not variable_name:
            raise NoVariableNameGivenError(type)

        self.type = type
        self.exception_handler = exception_handler
        self.timeout_ms = timeout_ms
        self.max_jobs_to_activate = max_jobs_to_activate
        self.max_running_jobs = max_running_jobs
        self.variables_to_fetch = variables_to_fetch
        self.single_value = single_value
        self.variable_name = variable_name
        self.before = async_tools.asyncify_all_functions(before)
        self.after = async_tools.asyncify_all_functions(after)
        self.job_parameter_name: Optional[str] = None

    def __repr__(self):
        return (
            f"TaskConfig(type={self.type}, exception_handler={self.exception_handler}, "
            f"timeout_ms={self.timeout_ms}, max_jobs_to_activate={self.max_jobs_to_activate}, "
            f"max_running_jobs={self.max_running_jobs}, variables_to_fetch={self.variables_to_fetch},"
            f"single_value={self.single_value}, variable_name={self.variable_name},"
            f"before={self.before}, after={self.after})"
        )
