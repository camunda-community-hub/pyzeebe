from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyzeebe.function_tools import Function
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.types import JobHandler


@dataclass()
class Task:
    original_function: Function[..., Any]
    job_handler: JobHandler
    config: TaskConfig

    @property
    def type(self) -> str:
        return self.config.type
