from typing import Awaitable, Callable

from pyzeebe.job.job import Job

ExceptionHandler = Callable[[Exception, Job], Awaitable]
