from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, Union

from typing_extensions import ParamSpec

Parameters = ParamSpec("Parameters")
ReturnType = TypeVar("ReturnType")

SyncFunction = Callable[Parameters, ReturnType]
AsyncFunction = Callable[Parameters, Awaitable[ReturnType]]
Function = Union[SyncFunction[Parameters, ReturnType], AsyncFunction[Parameters, ReturnType]]

DictFunction = Callable[Parameters, Awaitable[Optional[Dict[str, Any]]]]
