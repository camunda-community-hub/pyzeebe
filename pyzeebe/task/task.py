from __future__ import annotations

from typing import Any

from pyzeebe.function_tools import Function
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import JobHandler


class Task:
    def __init__(self, original_function: Function[..., Any], job_handler: JobHandler, config: TaskConfig) -> None:
        self.original_function = original_function
        self.job_handler = job_handler
        self.config = config

    @property
    def type(self) -> str:
        return self.config.type

    def __repr__(self) -> str:
        return (
            f"Task(config= {self.config}, original_function={self.original_function}, "
            f"job_handler={self.job_handler})"
        )
