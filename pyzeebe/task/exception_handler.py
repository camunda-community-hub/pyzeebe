from typing import Callable, Awaitable

from pyzeebe.job.job import Job

ExceptionHandler = Callable[[Exception, Job], Awaitable]
