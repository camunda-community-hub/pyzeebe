from typing import Callable

TaskDecorator = Callable[['TaskContext'], 'TaskContext']
