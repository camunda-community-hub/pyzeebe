from typing import Callable

from pyzeebe.job.job import Job
from pyzeebe.job.job_status_controller import JobStatusController

ExceptionHandler = Callable[[Exception, Job, JobStatusController], None]
