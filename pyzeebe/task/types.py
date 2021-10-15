from typing import Awaitable, Callable, Union

from pyzeebe import Job

DecoratorRunner = Callable[[Job], Awaitable[Job]]
JobHandler = Callable[[Job], Awaitable[Job]]

SyncTaskDecorator = Callable[[Job], Job]
AsyncTaskDecorator = Callable[[Job], Awaitable[Job]]
TaskDecorator = Union[SyncTaskDecorator, AsyncTaskDecorator]
