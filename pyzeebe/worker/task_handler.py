import logging
from abc import abstractmethod
from typing import Tuple, List, Callable

from pyzeebe.common.exceptions import TaskNotFound
from pyzeebe.decorators.zeebe_decorator_base import ZeebeDecoratorBase
from pyzeebe.job.job import Job
from pyzeebe.job.job_status_controller import JobStatusController
from pyzeebe.task.task import Task
from pyzeebe.task.task_decorator import TaskDecorator


def default_exception_handler(e: Exception, job: Job, controller: JobStatusController) -> None:
    logging.warning(f"Task type: {job.type} - failed job {job}. Error: {e}.")
    controller.failure(f"Failed job. Error: {e}")


class ZeebeTaskHandler(ZeebeDecoratorBase):
    def __init__(self, before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        """
        Args:
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
        """
        super().__init__(before, after)
        self.tasks: List[Task] = []

    @abstractmethod
    def task(self, task_type: str, exception_handler: Callable[
        [Exception, Job, JobStatusController], None] = default_exception_handler,
             before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        pass

    def remove_task(self, task_type: str) -> Task:
        task_index = self._get_task_index(task_type)
        return self.tasks.pop(task_index)

    def get_task(self, task_type: str) -> Task:
        return self._get_task_and_index(task_type)[0]

    def _get_task_index(self, task_type: str) -> int:
        return self._get_task_and_index(task_type)[-1]

    def _get_task_and_index(self, task_type: str) -> Tuple[Task, int]:
        for index, task in enumerate(self.tasks):
            if task.type == task_type:
                return task, index
        raise TaskNotFound(f"Could not find task {task_type}")
