from typing import Callable

from pyzeebe.job.job import Job

ExceptionHandler = Callable[[Exception, Job], None]
