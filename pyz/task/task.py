from typing import Callable, Dict, List

from pyz.base_types.base_decorator import BaseDecorator, TaskDecorator


class Task(BaseDecorator):
    def __init__(self, task_type: str, task_handler: Callable[[Dict], Dict], exception_handler: Callable,
                 before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        super().__init__(before=before, after=after)
        self.type = task_type
        self.handler = task_handler
        self.exception_handler = exception_handler
