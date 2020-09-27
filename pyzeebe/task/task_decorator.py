from typing import Callable

from pyzeebe.job.job import Job

TaskDecorator = Callable[[Job], Job]
