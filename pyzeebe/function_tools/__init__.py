from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Optional, TypeVar, Union

from typing_extensions import ParamSpec

Parameters = ParamSpec("Parameters")
ReturnType = TypeVar("ReturnType")

SyncFunction = Callable[Parameters, ReturnType]
AsyncFunction = Callable[Parameters, Awaitable[ReturnType]]
Function = Union[SyncFunction[Parameters, ReturnType], AsyncFunction[Parameters, ReturnType]]

DictFunction = Callable[Parameters, Awaitable[Optional[dict[str, Any]]]]
