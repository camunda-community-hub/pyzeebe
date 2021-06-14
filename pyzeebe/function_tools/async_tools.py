import asyncio
import functools
from typing import List

from pyzeebe.function_tools import AsyncFunction, Function, SyncFunction


def asyncify_all_functions(functions: List[Function]) -> List[AsyncFunction]:
    async_functions = []
    for function in functions:
        if not is_async_function(function):
            async_functions.append(asyncify(function))
        else:
            # Mypy doesn't correctly understand that this is an async function
            async_functions.append(function)  # type: ignore
    return async_functions


def asyncify(task_function: SyncFunction) -> AsyncFunction:
    @functools.wraps(task_function)
    async def async_function(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(task_function, *args, **kwargs))
    return async_function


def is_async_function(function: Function) -> bool:
    # Not using inspect.iscoroutinefunction here because it doens't handle AsyncMock well
    # See: https://bugs.python.org/issue40573
    return asyncio.iscoroutinefunction(function)
