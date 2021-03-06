import logging
from typing import List, Optional

from pyzeebe.exceptions import NoVariableNameGiven
from pyzeebe.job.job import Job
from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.types import TaskDecorator

logger = logging.getLogger(__name__)


def default_exception_handler(e: Exception, job: Job) -> None:
    logger.warning(f"Task type: {job.type} - failed job {job}. Error: {e}.")
    job.set_failure_status(f"Failed job. Error: {e}")


class TaskConfig:
    def __init__(self, type: str, exception_handler: ExceptionHandler = default_exception_handler,
                 timeout: int = 10000, max_jobs_to_activate: int = 32, variables_to_fetch: Optional[List[str]] = None,
                 single_value: bool = False, variable_name: Optional[str] = None, before: List[TaskDecorator] = None,
                 after: List[TaskDecorator] = None):
        if single_value and not variable_name:
            raise NoVariableNameGiven(type)

        self.type = type
        self.exception_handler = exception_handler
        self.timeout = timeout
        self.max_jobs_to_activate = max_jobs_to_activate
        self.variables_to_fetch = variables_to_fetch
        self.single_value = single_value
        self.variable_name = variable_name
        self.before = before or []
        self.after = after or []
