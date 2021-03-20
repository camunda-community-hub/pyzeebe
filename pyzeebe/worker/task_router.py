import logging
from typing import Callable, List, Tuple, Optional

from pyzeebe import TaskDecorator
from pyzeebe.errors import (DuplicateTaskTypeError, NoVariableNameGivenError,
                            TaskNotFoundError)
from pyzeebe.job.job import Job
from pyzeebe.task import task_builder
from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig

logger = logging.getLogger(__name__)


def default_exception_handler(e: Exception, job: Job) -> None:
    logger.warning(f"Task type: {job.type} - failed job {job}. Error: {e}.")
    job.set_failure_status(f"Failed job. Error: {e}")


class ZeebeTaskRouter:
    def __init__(self, before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        """
        Args:
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
        """
        self._before: List[TaskDecorator] = before or []
        self._after: List[TaskDecorator] = after or []
        self.tasks: List[Task] = []

    def task(self, task_type: str, exception_handler: ExceptionHandler = default_exception_handler,
             variables_to_fetch: Optional[List[str]] = None, timeout_ms: int = 10000, max_jobs_to_activate: int = 32,
             before: List[TaskDecorator] = None, after: List[TaskDecorator] = None, single_value: bool = False,
             variable_name: str = None):
        """
        Decorator to create a task
        Args:
            task_type (str): The task type

            exception_handler (ExceptionHandler): Handler that will be called when a job fails. 

            variables_to_fetch (Optional[List[str]]): The variables to request from Zeebe when activating jobs.

            timeout_ms (int): Maximum duration of the task in milliseconds. If the timeout is surpassed Zeebe will give up 
                                on the worker and retry it. Default: 10000 (10 seconds).

            max_jobs_to_activate (int):  Maximum jobs the worker will execute in parallel (of this task). Default: 32

            before (List[TaskDecorator]): All decorators which should be performed before the task.

            after (List[TaskDecorator]): All decorators which should be performed after the task.

            single_value (bool): If the function returns a single value (int, string, list) and not a dictionary set
                                 this to True. Default: False

            variable_name (str): If single_value then this will be the variable name given to zeebe:
                                        { <variable_name>: <function_return_value> }
        Raises:
            DuplicateTaskTypeError: If a task from the router already exists in the worker
            NoVariableNameGivenError: When single_value is set, but no variable_name is given
        """
        if single_value and not variable_name:
            raise NoVariableNameGivenError(task_type)

        def task_wrapper(task_function: Callable):
            config = TaskConfig(
                task_type,
                exception_handler,
                timeout_ms,
                max_jobs_to_activate,
                variables_to_fetch or task_builder.get_parameters_from_function(
                    task_function),
                single_value,
                variable_name or "",
                before or [],
                after or []
            )
            config_with_decorators = self._add_decorators_to_config(config)

            task = task_builder.build_task(
                task_function, config_with_decorators
            )
            self._add_task(task)
            return task_function

        return task_wrapper

    def _add_task(self, task: Task):
        self._is_task_duplicate(task.type)
        self.tasks.append(task)

    def _add_decorators_to_config(self, config: TaskConfig) -> TaskConfig:
        before_decorators = self._before.copy()
        before_decorators.extend(config.before)
        config.before = before_decorators
        config.after.extend(self._after)
        return config

    def _is_task_duplicate(self, task_type: str) -> None:
        try:
            self.get_task(task_type)
            raise DuplicateTaskTypeError(task_type)
        except TaskNotFoundError:
            return

    def before(self, *decorators: TaskDecorator) -> None:
        """
        Add decorators to be performed before a job is run

        Args:
            decorators (Iterable[TaskDecorator]): The decorators to be performed before each job is run
        """
        self._before.extend(decorators)

    def after(self, *decorators: TaskDecorator) -> None:
        """
        Add decorators to be performed after a job is run

        Args:
            decorators (Iterable[TaskDecorator]): The decorators to be performed after each job is run
        """
        self._after.extend(decorators)

    def remove_task(self, task_type: str) -> Task:
        """
        Remove a task

        Args:
            task_type (str): The type of the wanted task

        Returns:
            Task: The task that was removed

        Raises:
             TaskNotFoundError: If no task with specified type exists

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
             TaskNotFoundError: If no task with specified type exists

        """
        return self._get_task_and_index(task_type)[0]

    def _get_task_index(self, task_type: str) -> int:
        return self._get_task_and_index(task_type)[1]

    def _get_task_and_index(self, task_type: str) -> Tuple[Task, int]:
        for index, task in enumerate(self.tasks):
            if task.type == task_type:
                return task, index
        raise TaskNotFoundError(f"Could not find task {task_type}")
