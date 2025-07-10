from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

from typing_extensions import TypeIs

from pyzeebe import errors
from pyzeebe.function_tools import Function
from pyzeebe.job.job import Job

try:
    import pydantic
except ImportError:
    pydantic = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from pydantic import BaseModel


logger = logging.getLogger(__name__)


def _is_pydantic_model(cls: type) -> TypeIs[type[BaseModel]]:
    return bool(pydantic and issubclass(cls, pydantic.BaseModel))


def get_parameters_from_function(task_function: Function[..., Any]) -> list[str] | None:
    function_signature = inspect.signature(task_function)
    for _, parameter in function_signature.parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            return []

    if not function_signature.parameters:
        return None

    if all(param.annotation == Job for param in function_signature.parameters.values()):
        return []

    if pydantic:
        pydantic_schemas = [
            (param.name, param.annotation)
            for param in function_signature.parameters.values()
            if _is_pydantic_model(param.annotation)
        ]

        if len(pydantic_schemas) > 1:
            raise errors.PyZeebeError("Only one Pydantic schema is allowed")
        elif len(pydantic_schemas) == 1:
            if any(
                not (param.annotation == Job or _is_pydantic_model(param.annotation))
                for param in function_signature.parameters.values()
            ):
                logger.warning("Additional arguments when used pydantic schema is not allowed")
            return list(pydantic_schemas[0][1].__pydantic_fields__.keys())

    return [param.name for param in function_signature.parameters.values() if param.annotation != Job]


def get_job_parameter_name(function: Function[..., Any]) -> str | None:
    function_signature = inspect.signature(function)
    params = list(function_signature.parameters.values())
    for param in params:
        if param.annotation == Job:
            return param.name
    return None


def get_pydantic_schema(function: Function[..., Any]) -> tuple[str, type[BaseModel]] | None:
    if not pydantic:
        return None

    function_signature = inspect.signature(function)
    params = list(function_signature.parameters.values())

    for param in params:
        if issubclass(param.annotation, pydantic.BaseModel):
            return param.name, param.annotation

    return None
