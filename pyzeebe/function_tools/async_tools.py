from __future__ import annotations

import asyncio
import functools
from collections.abc import Iterable
from typing import Any, TypeVar

from typing_extensions import ParamSpec, TypeIs

from pyzeebe.function_tools import AsyncFunction, Function, SyncFunction

P = ParamSpec("P")
R = TypeVar("R")


def asyncify_all_functions(functions: Iterable[Function[..., Any]]) -> list[AsyncFunction[..., Any]]:
    async_functions: list[AsyncFunction[..., Any]] = []
    for function in functions:
        if not is_async_function(function):
            async_functions.append(asyncify(function))
        else:
            async_functions.append(function)
    return async_functions


def asyncify(task_function: SyncFunction[P, R]) -> AsyncFunction[P, R]:
    @functools.wraps(task_function)
    async def async_function(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(task_function, *args, **kwargs))

    return async_function


def is_async_function(function: Function[P, R]) -> TypeIs[AsyncFunction[P, R]]:
    # Not using inspect.iscoroutinefunction here because it doens't handle AsyncMock well
    # See: https://bugs.python.org/issue40573
    return asyncio.iscoroutinefunction(function)
