from typing import Callable, List, Dict

from pyz.decorators.base_zeebe_decorator import BaseZeebeDecorator
from pyz.task.task_context import TaskContext
from pyz.task.task_status_setter import TaskStatusSetter


class Task(BaseZeebeDecorator):
    def __init__(self, task_type: str, task_handler: Callable[..., Dict],
                 exception_handler: Callable[[Exception, TaskContext, TaskStatusSetter], None],
                 timeout: int = 0, max_jobs_to_activate: int = 32, variables_to_fetch: List[str] = None,
                 before: List = None, after: List = None):
        super().__init__(before=before, after=after)

        self.type = task_type
        self.inner_function = task_handler
        self.exception_handler = exception_handler
        self.timeout = timeout
        self.max_jobs_to_activate = max_jobs_to_activate
        self.variables_to_fetch = variables_to_fetch or []
        self.handler: Callable[[TaskContext], TaskContext] = None
