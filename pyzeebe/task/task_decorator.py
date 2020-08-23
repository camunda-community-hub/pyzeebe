from typing import Callable

from pyzeebe.task.task_context import TaskContext

TaskDecorator = Callable[[TaskContext], TaskContext]
