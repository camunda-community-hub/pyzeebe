from collections.abc import Awaitable
from typing import Callable, Union

from pyzeebe import Job
from pyzeebe.job.job import JobController

DecoratorRunner = Callable[[Job], Awaitable[Job]]
JobHandler = Callable[[Job, JobController], Awaitable[Job]]

SyncTaskDecorator = Callable[[Job], Job]
AsyncTaskDecorator = Callable[[Job], Awaitable[Job]]
TaskDecorator = Union[SyncTaskDecorator, AsyncTaskDecorator]
