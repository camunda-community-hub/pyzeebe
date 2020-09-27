from typing import List, Callable, Dict

from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.task import Task
from pyzeebe.task.task_decorator import TaskDecorator
from pyzeebe.worker.task_handler import ZeebeTaskHandler, default_exception_handler


class ZeebeTaskRouter(ZeebeTaskHandler):
    def _dict_task(self, task_type: str, exception_handler: ExceptionHandler = default_exception_handler,
                   before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        def wrapper(fn: Callable[..., Dict]):
            task = self._create_task(task_type=task_type, task_handler=fn, exception_handler=exception_handler,
                                     before=before, after=after)

            self.tasks.append(task)
            return fn

        return wrapper

    def _non_dict_task(self, task_type: str, variable_name: str,
                       exception_handler: ExceptionHandler = default_exception_handler,
                       before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        def wrapper(fn: Callable[..., Dict]):
            dict_fn = self._single_value_function_to_dict(variable_name=variable_name, fn=fn)

            task = self._create_task(task_type=task_type, task_handler=dict_fn, exception_handler=exception_handler,
                                     before=before, after=after)

            self.tasks.append(task)
            return fn

        return wrapper

    def _create_task(self, task_type: str, task_handler: Callable, exception_handler: ExceptionHandler,
                     before: List[TaskDecorator] = None, after: List[TaskDecorator] = None) -> Task:
        task = Task(task_type=task_type, task_handler=task_handler, exception_handler=exception_handler)
        return self._add_decorators_to_task(task, before or [], after or [])

    def _add_decorators_to_task(self, task: Task, before: List[TaskDecorator],
                                after: List[TaskDecorator]) -> Task:
        before_decorators = self._before.copy()
        before_decorators.extend(before)

        after.extend(self._after)

        task.before(*before_decorators)
        task.after(*after)
        return task
