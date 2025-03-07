from collections.abc import Awaitable
from typing import Callable

from pyzeebe import Job
from pyzeebe.job.job import JobController

JobHandler = Callable[[Job, JobController], Awaitable[Job]]
