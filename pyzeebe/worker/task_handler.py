import logging
from abc import abstractmethod
from typing import Tuple, List, Callable, Dict

from pyzeebe.decorators.zeebe_decorator_base import ZeebeDecoratorBase
from pyzeebe.exceptions import NoVariableNameGiven, TaskNotFound, DuplicateTaskType
from pyzeebe.job.job import Job
from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.task import Task
from pyzeebe.task.task_decorator import TaskDecorator


logger = logging.getLogger(__name__)

def default_exception_handler(e: Exception, job: Job) -> None:
    logger.warning(f"Task type: {job.type} - failed job {job}. Error: {e}.")
    job.set_failure_status(f"Failed job. Error: {e}")


class ZeebeTaskHandler(ZeebeDecoratorBase):
    def __init__(self, before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        """
        Args:
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
        """
        super().__init__(before, after)
        self.tasks: List[Task] = []

    def task(self, task_type: str, exception_handler: ExceptionHandler = default_exception_handler,
             variables_to_fetch: List[str] = None, timeout: int = 10000, max_jobs_to_activate: int = 32,
             before: List[TaskDecorator] = None, after: List[TaskDecorator] = None, single_value: bool = False,
             variable_name: str = None):
        """
        Decorator to create a task

        Args:
            before (List[TaskDecorator]): All decorators which should be performed before the task.
            after (List[TaskDecorator]): All decorators which should be performed after the task.
            timeout (int): How long Zeebe should wait before the job is retried. Default: 10000 milliseconds
            single_value (bool): If the function returns a single value (int, string, list) and not a dictionary set
                                 this to True. Default: False
            variable_name (str): If single_value then this will be the variable name given to zeebe:
                                        { <variable_name>: <function_return_value> }
            timeout (int): Maximum duration of the task in milliseconds. If the timeout is surpasses Zeebe will give up
                            on the job and retry it. Default: 10000
            max_jobs_to_activate (int):  Maximum jobs the worker will execute in parallel (of this task). Default: 32

        Raises:
            DuplicateTaskType: If a task from the router already exists in the worker

        """
        self._is_task_duplicate(task_type)

        if single_value and not variable_name:
            raise NoVariableNameGiven(task_type=task_type)

        elif single_value and variable_name:
            return self._non_dict_task(task_type=task_type, variable_name=variable_name, timeout=timeout,
                                       max_jobs_to_activate=max_jobs_to_activate, exception_handler=exception_handler,
                                       before=before, after=after, variables_to_fetch=variables_to_fetch)

        else:
            return self._dict_task(task_type=task_type, exception_handler=exception_handler, before=before, after=after,
                                   timeout=timeout, max_jobs_to_activate=max_jobs_to_activate,
                                   variables_to_fetch=variables_to_fetch)

    @abstractmethod
    def _dict_task(self, task_type: str, exception_handler: ExceptionHandler = default_exception_handler,
                   timeout: int = 10000, max_jobs_to_activate: int = 32, before: List[TaskDecorator] = None,
                   after: List[TaskDecorator] = None, variables_to_fetch: List[str] = None):
        raise NotImplemented()

    @abstractmethod
    def _non_dict_task(self, task_type: str, variable_name: str,
                       exception_handler: ExceptionHandler = default_exception_handler, timeout: int = 10000,
                       max_jobs_to_activate: int = 32, before: List[TaskDecorator] = None,
                       after: List[TaskDecorator] = None, variables_to_fetch: List[str] = None):
        raise NotImplemented()

    @staticmethod
    def _single_value_function_to_dict(variable_name: str, fn: Callable) -> Callable[..., Dict]:
        def inner_fn(*args, **kwargs):
            return {variable_name: fn(*args, **kwargs)}

        return inner_fn

    @staticmethod
    def _get_parameters_from_function(fn: Callable) -> List[str]:
        parameters = fn.__code__.co_varnames
        if "args" in parameters:
            return []
        elif "kwargs" in parameters:
            return []
        else:
            return list(parameters)

    def _is_task_duplicate(self, task_type: str) -> None:
        try:
            self.get_task(task_type)
            raise DuplicateTaskType(task_type)
        except TaskNotFound:
            return

    def remove_task(self, task_type: str) -> Task:
        """
        Remove a task

        Args:
            task_type (str): The type of the wanted task

        Returns:
            Task: The task that was removed

        Raises:
             TaskNotFound: If no task with specified type exists

        """
        task_index = self._get_task_index(task_type)
        return self.tasks.pop(task_index)

    def get_task(self, task_type: str) -> Task:
        """
        Get a task by its type

        Args:
            task_type (str): The type of the wanted task

        Returns:
            Task: The wanted task

        Raises:
             TaskNotFound: If no task with specified type exists

        """
        return self._get_task_and_index(task_type)[0]

    def _get_task_index(self, task_type: str) -> int:
        return self._get_task_and_index(task_type)[-1]

    def _get_task_and_index(self, task_type: str) -> Tuple[Task, int]:
        for index, task in enumerate(self.tasks):
            if task.type == task_type:
                return task, index
        raise TaskNotFound(f"Could not find task {task_type}")
