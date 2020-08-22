from typing import Callable

from pyz.task.job_context import JobContext

TaskDecorator = Callable[[JobContext], JobContext]
