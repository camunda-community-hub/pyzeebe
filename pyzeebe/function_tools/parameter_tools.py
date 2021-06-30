import inspect
from typing import List, Optional

from pyzeebe.function_tools import Function
from pyzeebe.job.job import Job


def get_parameters_from_function(task_function: Function) -> List[str]:
    function_signature = inspect.signature(task_function)
    for _, parameter in function_signature.parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            return []
    return list(function_signature.parameters)


def get_job_parameter_name(function: Function) -> Optional[str]:
    function_signature = inspect.signature(function)
    params = list(function_signature.parameters.values())
    for param in params:
        if param.annotation == Job:
            return param.name
    return None
