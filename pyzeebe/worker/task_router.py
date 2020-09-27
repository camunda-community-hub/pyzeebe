from typing import List, Callable, Dict

from pyzeebe.job.job import Job
from pyzeebe.job.job_status_controller import JobStatusController
from pyzeebe.task.task import Task
from pyzeebe.task.task_decorator import TaskDecorator
from pyzeebe.worker.task_handler import ZeebeTaskHandler, default_exception_handler


class ZeebeTaskRouter(ZeebeTaskHandler):
    def task(self, task_type: str, exception_handler: Callable[
        [Exception, Job, JobStatusController], None] = default_exception_handler,
             before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        def wrapper(fn: Callable[..., Dict]):
            before_decorators = self._before.copy()
            before_decorators.extend(before or [])
            after_decorators = self._after.copy()
            after_decorators.extend(after or [])

            task = Task(task_type=task_type, task_handler=fn, exception_handler=exception_handler,
                        before=before_decorators, after=after_decorators)
            self.tasks.append(task)
            return fn

        return wrapper
