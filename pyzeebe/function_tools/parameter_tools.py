from __future__ import annotations

import inspect
from typing import Any, get_type_hints

from typing_extensions import (  # type: ignore[attr-defined]
    _is_unpack,
    get_args,
    is_typeddict,
)

from pyzeebe.function_tools import Function
from pyzeebe.job.job import Job


def get_parameters_from_function(task_function: Function[..., Any]) -> list[str] | None:
    variables_to_fetch: list[str] = []

    function_signature = inspect.signature(task_function)
    if not function_signature.parameters:
        return None

    for parameter in function_signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            return []
        elif parameter.kind == inspect.Parameter.VAR_KEYWORD:
            if _is_unpack(parameter.annotation) and is_typeddict(get_args(parameter.annotation)[0]):
                variables_to_fetch.extend(get_type_hints(get_args(parameter.annotation)[0]).keys())
            else:
                return []
        elif parameter.annotation != Job:
            variables_to_fetch.append(parameter.name)

    if all(param.annotation == Job for param in function_signature.parameters.values()):
        return []

    return variables_to_fetch


def get_job_parameter_name(function: Function[..., Any]) -> str | None:
    function_signature = inspect.signature(function)
    params = list(function_signature.parameters.values())
    for param in params:
        if param.annotation == Job:
            return param.name
    return None
