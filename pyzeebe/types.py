from __future__ import annotations

from collections.abc import Awaitable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable, Protocol, Union

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from pyzeebe import Job, JobController
    from pyzeebe.task.task import Task


JsonType: TypeAlias = Union[Mapping[str, "JsonType"], Sequence["JsonType"], str, int, float, bool, None]
JsonDictType: TypeAlias = Mapping[str, JsonType]

Headers: TypeAlias = Mapping[str, Any]
Variables: TypeAlias = JsonDictType
Unset = "UNSET"

ChannelArgumentType: TypeAlias = Sequence[tuple[str, Any]]

JobHandler: TypeAlias = Callable[["Job", "JobController"], Awaitable[Variables]]
ExceptionHandler: TypeAlias = Callable[[Exception, "Job", "JobController"], Awaitable[None]]


class MiddlewareProto(Protocol):
    async def __call__(
        self, job: Job, job_controller: JobController, *, task: Task, call_next: JobHandler
    ) -> Variables: ...
