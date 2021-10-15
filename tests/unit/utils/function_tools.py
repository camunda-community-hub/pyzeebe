from typing import Callable, List

from pyzeebe.function_tools import async_tools


def functions_are_all_async(functions: List[Callable]) -> bool:
    return all(
        [
            async_tools.is_async_function(function)
            for function
            in functions
        ]
    )
