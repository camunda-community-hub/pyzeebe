from typing import Callable

from zeebepy.task.job_context import JobContext

TaskDecorator = Callable[[JobContext], JobContext]
