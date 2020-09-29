from typing import List, Callable, Dict

from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.task import Task
from pyzeebe.task.task_decorator import TaskDecorator
from pyzeebe.worker.task_handler import ZeebeTaskHandler, default_exception_handler


class ZeebeTaskRouter(ZeebeTaskHandler):
    def _dict_task(self, task_type: str, exception_handler: ExceptionHandler = default_exception_handler,
                   timeout: int = 10000, max_jobs_to_activate: int = 32, before: List[TaskDecorator] = None,
                   after: List[TaskDecorator] = None, variables_to_fetch: List[str] = None):
        def wrapper(fn: Callable[..., Dict]):
            nonlocal variables_to_fetch
            if not variables_to_fetch:
                variables_to_fetch = self._get_parameters_from_function(fn)

            task = self._create_task(task_type=task_type, task_handler=fn, exception_handler=exception_handler,
                                     timeout=timeout, max_jobs_to_activate=max_jobs_to_activate, before=before,
                                     after=after, variables_to_fetch=variables_to_fetch)

            self.tasks.append(task)
            return fn

        return wrapper

    def _non_dict_task(self, task_type: str, variable_name: str,
                       exception_handler: ExceptionHandler = default_exception_handler, timeout: int = 10000,
                       max_jobs_to_activate: int = 32, before: List[TaskDecorator] = None,
                       after: List[TaskDecorator] = None, variables_to_fetch: List[str] = None):
        def wrapper(fn: Callable[..., Dict]):
            nonlocal variables_to_fetch
            if not variables_to_fetch:
                variables_to_fetch = self._get_parameters_from_function(fn)

            dict_fn = self._single_value_function_to_dict(variable_name=variable_name, fn=fn)

            task = self._create_task(task_type=task_type, task_handler=dict_fn, exception_handler=exception_handler,
                                     timeout=timeout, max_jobs_to_activate=max_jobs_to_activate, before=before,
                                     after=after, variables_to_fetch=variables_to_fetch)

            self.tasks.append(task)
            return fn

        return wrapper

    def _create_task(self, task_type: str, task_handler: Callable, exception_handler: ExceptionHandler,
                     timeout: int = 10000, max_jobs_to_activate: int = 32, before: List[TaskDecorator] = None,
                     after: List[TaskDecorator] = None, variables_to_fetch: List[str] = None) -> Task:
        task = Task(task_type=task_type, task_handler=task_handler, exception_handler=exception_handler,
                    timeout=timeout, max_jobs_to_activate=max_jobs_to_activate, variables_to_fetch=variables_to_fetch)
        return self._add_decorators_to_task(task, before or [], after or [])

    def _add_decorators_to_task(self, task: Task, before: List[TaskDecorator],
                                after: List[TaskDecorator]) -> Task:
        before_decorators = self._before.copy()
        before_decorators.extend(before)

        after.extend(self._after)

        task.before(*before_decorators)
        task.after(*after)
        return task
