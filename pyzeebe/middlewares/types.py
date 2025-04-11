from collections.abc import Awaitable, Callable

from pyzeebe.job.job import Job, JobController

ConsumeMiddlewareStack = Callable[[Job], Awaitable[Job]]
ExecuteMiddlewareStack = Callable[[Job, JobController], Awaitable[Job]]
