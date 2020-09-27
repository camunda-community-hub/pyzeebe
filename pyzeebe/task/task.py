from typing import Callable, List, Dict

from pyzeebe.decorators.zeebe_decorator_base import ZeebeDecoratorBase
from pyzeebe.job.job import Job
from pyzeebe.task.exception_handler import ExceptionHandler


class Task(ZeebeDecoratorBase):
    def __init__(self, task_type: str, task_handler: Callable[..., Dict], exception_handler: ExceptionHandler,
                 timeout: int = 10000, max_jobs_to_activate: int = 32, variables_to_fetch: List[str] = None,
                 before: List = None, after: List = None):
        super().__init__(before=before, after=after)

        self.type = task_type
        self.inner_function = task_handler
        self.exception_handler = exception_handler
        self.timeout = timeout
        self.max_jobs_to_activate = max_jobs_to_activate
        self.variables_to_fetch = variables_to_fetch or []
        self.handler: Callable[[Job], Job] = None

    def __repr__(self) -> str:
        return str({"type": self.type, "timeout": self.timeout, "max_jobs_to_activate": self.max_jobs_to_activate,
                    "variables_to_fetch": self.variables_to_fetch})
