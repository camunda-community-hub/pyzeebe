from __future__ import annotations

import functools
from typing import Any, TypeVar

from typing_extensions import ParamSpec

from pyzeebe.function_tools import AsyncFunction, DictFunction

P = ParamSpec("P")
R = TypeVar("R")


def convert_to_dict_function(single_value_function: AsyncFunction[P, R], variable_name: str) -> DictFunction[P]:
    @functools.wraps(single_value_function)
    async def inner_fn(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        return {variable_name: await single_value_function(*args, **kwargs)}

    return inner_fn
