from typing import Callable

from pyz.task.task_context import TaskContext

TaskDecorator = Callable[[TaskContext], TaskContext]
