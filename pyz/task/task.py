from typing import Callable, List, Dict

from pyz.decorators.base_zeebe_decorator import BaseZeebeDecorator
from pyz.task.task_context import TaskContext


class Task(BaseZeebeDecorator):
    def __init__(self, task_type: str, task_handler: Callable[..., Dict],
                 exception_handler: Callable[[TaskContext], None],
                 timeout: int = 0, max_jobs_to_activate: int = 5, variables_to_fetch: List[str] = None,
                 before: List = None, after: List = None):
        super().__init__(before=before, after=after)

        self.type = task_type
        self.original_handler = task_handler
        self.exception_handler = exception_handler
        self.timeout = timeout
        self.max_jobs_to_activate = max_jobs_to_activate
        self.variables_to_fetch = variables_to_fetch or []
        self.handler: Callable[[TaskContext], TaskContext] = None
