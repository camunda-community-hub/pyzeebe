from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any, Callable, Literal, Optional, TypeVar, overload

from typing_extensions import ParamSpec

from pyzeebe.errors import DuplicateTaskTypeError, TaskNotFoundError
from pyzeebe.function_tools import Function, parameter_tools
from pyzeebe.task import task_builder
from pyzeebe.task.exception_handler import ExceptionHandler
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import TaskDecorator

P = ParamSpec("P")
R = TypeVar("R")
RD = TypeVar("RD", bound=Optional[dict[str, Any]])

logger = logging.getLogger(__name__)


class ZeebeTaskRouter:
    def __init__(
        self,
        before: list[TaskDecorator] | None = None,
        after: list[TaskDecorator] | None = None,
        exception_handler: ExceptionHandler | None = None,
    ):
        """
        Args:
            before (List[TaskDecorator]): Decorators to be performed before each task
            after (List[TaskDecorator]): Decorators to be performed after each task
            exception_handler (ExceptionHandler): Handler that will be called when a job fails.
        """
        self._exception_handler = exception_handler
        self._before: list[TaskDecorator] = before or []
        self._after: list[TaskDecorator] = after or []
        self.tasks: list[Task] = []

    @overload
    def task(
        self,
        task_type: str,
        exception_handler: ExceptionHandler | None = None,
        variables_to_fetch: Iterable[str] | None = None,
        timeout_ms: int = 10000,
        max_jobs_to_activate: int = 32,
        max_running_jobs: int = 32,
        before: list[TaskDecorator] | None = None,
        after: list[TaskDecorator] | None = None,
        *,
        single_value: Literal[False] = False,
    ) -> Callable[[Function[P, RD]], Function[P, RD]]: ...

    @overload
    def task(
        self,
        task_type: str,
        exception_handler: ExceptionHandler | None = None,
        variables_to_fetch: Iterable[str] | None = None,
        timeout_ms: int = 10000,
        max_jobs_to_activate: int = 32,
        max_running_jobs: int = 32,
        before: list[TaskDecorator] | None = None,
        after: list[TaskDecorator] | None = None,
        *,
        single_value: Literal[True],
        variable_name: str,
    ) -> Callable[[Function[P, R]], Function[P, R]]: ...

    def task(
        self,
        task_type: str,
        exception_handler: ExceptionHandler | None = None,
        variables_to_fetch: Iterable[str] | None = None,
        timeout_ms: int = 10000,
        max_jobs_to_activate: int = 32,
        max_running_jobs: int = 32,
        before: list[TaskDecorator] | None = None,
        after: list[TaskDecorator] | None = None,
        single_value: bool = False,
        variable_name: str | None = None,
    ) -> Callable[[Function[P, R]], Function[P, R]]:
        """
        Decorator to create a task

        Args:
            task_type (str): The task type
            exception_handler (ExceptionHandler): Handler that will be called when a job fails.
            variables_to_fetch (Optional[Iterable[str]]): The variables to request from Zeebe when activating jobs.
            timeout_ms (int): Maximum duration of the task in milliseconds. If the timeout is surpassed Zeebe will give up
                                on the worker and retry it. Default: 10000 (10 seconds).
            max_jobs_to_activate (int):  Maximum amount of jobs the worker will activate in one request to the Zeebe gateway. Default: 32
            max_running_jobs (int): Maximum amount of jobs that will run simultaneously. Default: 32
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
        _exception_handler = exception_handler or self._exception_handler

        def task_wrapper(task_function: Function[P, R]) -> Function[P, R]:
            config = TaskConfig(
                task_type,
                _exception_handler,
                timeout_ms,
                max_jobs_to_activate,
                max_running_jobs,
                variables_to_fetch or parameter_tools.get_parameters_from_function(task_function),
                single_value,
                variable_name or "",
                before or [],
                after or [],
            )
            config_with_decorators = self._add_decorators_to_config(config)

            task = task_builder.build_task(task_function, config_with_decorators)
            self._add_task(task)
            return task_function

        return task_wrapper

    def _add_task(self, task: Task) -> None:
        self._is_task_duplicate(task.type)
        self.tasks.append(task)

    def _add_decorators_to_config(self, config: TaskConfig) -> TaskConfig:
        new_task_config = TaskConfig(
            type=config.type,
            exception_handler=config.exception_handler or self._exception_handler,
            timeout_ms=config.timeout_ms,
            max_jobs_to_activate=config.max_jobs_to_activate,
            max_running_jobs=config.max_running_jobs,
            variables_to_fetch=config.variables_to_fetch,
            single_value=config.single_value,
            variable_name=config.variable_name,
            before=self._before + config.before,  # type: ignore
            after=config.after + self._after,  # type: ignore
        )
        return new_task_config

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

    def exception_handler(self, exception_handler: ExceptionHandler) -> None:
        """
        Add exception handler to be called when a job fails

        Args:
            exception_handler (ExceptionHandler): Handler that will be called when a job fails.
        """
        self._exception_handler = exception_handler

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

    def _get_task_and_index(self, task_type: str) -> tuple[Task, int]:
        for index, task in enumerate(self.tasks):
            if task.type == task_type:
                return task, index
        raise TaskNotFoundError(f"Could not find task {task_type}")
