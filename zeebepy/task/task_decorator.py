from typing import Callable

from zeebepy.task.task_context import TaskContext

TaskDecorator = Callable[[TaskContext], TaskContext]
