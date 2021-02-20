from dataclasses import dataclass

from pyzeebe.task.types import JobHandler
from pyzeebe.task.task_config import TaskConfig


@dataclass
class Task:
    job_handler: JobHandler
    config: TaskConfig

    @property
    def type(self):
        return self.config.type
