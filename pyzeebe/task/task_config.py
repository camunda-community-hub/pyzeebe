from __future__ import annotations

from dataclasses import dataclass

from pyzeebe.errors import NoVariableNameGivenError


@dataclass()
class TaskConfig:
    type: str
    timeout_ms: int
    max_jobs_to_activate: int
    max_running_jobs: int
    variables_to_fetch: list[str] | None
    single_value: bool
    variable_name: str
    job_parameter_name: str | None = None

    def __post_init__(self) -> None:
        if self.single_value and not self.variable_name:
            raise NoVariableNameGivenError(self.type)
