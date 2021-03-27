from typing import Callable

from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import JobHandler


class Task:
    def __init__(self, original_function: Callable, job_handler: JobHandler, config: TaskConfig):
        self.original_function = original_function
        self.job_handler = job_handler
        self.config = config

    @property
    def type(self):
        return self.config.type

    def __repr__(self):
        return f"Task(config= {self.config}, original_function={self.original_function}, " \
               f"job_handler={self.job_handler})"
