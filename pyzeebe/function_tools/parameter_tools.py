import inspect
from typing import List

from pyzeebe.function_tools import Function


def get_parameters_from_function(task_function: Function) -> List[str]:
    function_signature = inspect.signature(task_function)
    for _, parameter in function_signature.parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            return []
    return list(function_signature.parameters)
