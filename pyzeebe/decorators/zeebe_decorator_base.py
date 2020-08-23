from typing import List

from pyzeebe.task.task_decorator import TaskDecorator


class ZeebeDecoratorBase(object):
    def __init__(self, before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        self._before: List[TaskDecorator] = before or []
        self._after: List[TaskDecorator] = after or []

    def before(self, *decorators: TaskDecorator) -> None:
        self._before.extend(decorators)

    def after(self, *decorators: TaskDecorator) -> None:
        self._after.extend(decorators)
