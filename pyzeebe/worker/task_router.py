import logging
from typing import Tuple, List, Callable, Union

from pyzeebe import TaskDecorator
from pyzeebe.exceptions import TaskNotFoundError, DuplicateTaskType
from pyzeebe.task import task_builder
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig

logger = logging.getLogger(__name__)


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

    def task(self, task_config: Union[TaskConfig, str]):
        """
        Decorator to create a task

        Args:
            task_config (Union[str, TaskConfig]): Either the task type or a task configuration object

        Raises:
            DuplicateTaskType: If a task from the router already exists in the worker

        """
        if isinstance(task_config, str):
            task_config = TaskConfig(task_config)
        config_with_decorators = self._add_decorators_to_config(task_config)

        def wrapper(fn: Callable):
            task = task_builder.build_task(fn, config_with_decorators)
            self._add_task(task)
            return fn

        return wrapper

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
            raise DuplicateTaskType(task_type)
        except TaskNotFoundError:
            return

    def before(self, *decorators: TaskDecorator) -> None:
        self._before.extend(decorators)

    def after(self, *decorators: TaskDecorator) -> None:
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
