from dataclasses import dataclass
from typing import Callable

from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import JobHandler


@dataclass
class Task:
    original_function: Callable
    job_handler: JobHandler
    config: TaskConfig

    @property
    def type(self):
        return self.config.type
