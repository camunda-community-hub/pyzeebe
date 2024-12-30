from __future__ import annotations

from collections.abc import Awaitable
from typing import Callable, Optional, TypeVar, Union

from typing_extensions import ParamSpec, TypeAlias

from pyzeebe.types import JsonDictType

Parameters = ParamSpec("Parameters")
ReturnType = TypeVar("ReturnType")

SyncFunction: TypeAlias = Callable[Parameters, ReturnType]
AsyncFunction: TypeAlias = Callable[Parameters, Awaitable[ReturnType]]
Function: TypeAlias = Union[SyncFunction[Parameters, ReturnType], AsyncFunction[Parameters, ReturnType]]

DictFunction: TypeAlias = Callable[Parameters, Awaitable[Optional[JsonDictType]]]
