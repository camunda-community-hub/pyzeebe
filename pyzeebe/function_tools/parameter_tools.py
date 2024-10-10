from __future__ import annotations

import inspect
from typing import Any

from pyzeebe.function_tools import Function
from pyzeebe.job.job import Job


def get_parameters_from_function(task_function: Function[..., Any]) -> list[str] | None:
    function_signature = inspect.signature(task_function)
    for _, parameter in function_signature.parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            return []

    if not function_signature.parameters:
        return None

    if all(param.annotation == Job for param in function_signature.parameters.values()):
        return []

    return [param.name for param in function_signature.parameters.values() if param.annotation != Job]


def get_job_parameter_name(function: Function[..., Any]) -> str | None:
    function_signature = inspect.signature(function)
    params = list(function_signature.parameters.values())
    for param in params:
        if param.annotation == Job:
            return param.name
    return None
