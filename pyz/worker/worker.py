from typing import List, Tuple

from pyz.base_types.base import ZeebeBase
from pyz.base_types.base_decorator import BaseDecorator, TaskDecorator
from pyz.exceptions import TaskNotFoundException
from pyz.task import Task


class ZeebeWorker(ZeebeBase, BaseDecorator):
    def __init__(self, hostname: str = None, port: int = None, before: List[TaskDecorator] = None,
                 after: List[TaskDecorator] = None):
        ZeebeBase.__init__(self, hostname=hostname, port=port)
        BaseDecorator.__init__(self, before=before, after=after)
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task_type: str) -> Task:
        task, index = self.get_task(task_type)
        return self.tasks.pop(index)

    def get_task(self, task_type: str) -> Tuple[Task, int]:
        for index, task in enumerate(self.tasks):
            if self._is_task_of_type(task, task_type):
                return task, index
        raise TaskNotFoundException(f"Could not find task {task_type}")

    def work(self) -> None:
        pass

    def create_handler(self, task: Task):
        pass

    @staticmethod
    def _is_task_of_type(task: Task, task_type: str) -> bool:
        return task.type == task_type
