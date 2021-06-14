from typing import Awaitable, Callable, Dict, TypeVar, Union

Parameters = TypeVar("Parameters")
ReturnType = TypeVar("ReturnType")

SyncFunction = Callable[[Parameters], ReturnType]
AsyncFunction = Callable[[Parameters], Awaitable[ReturnType]]
Function = Union[SyncFunction, AsyncFunction]

DictFunction = Callable[[Parameters], Awaitable[Dict]]
