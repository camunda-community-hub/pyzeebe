from typing import List, Generic, TypeVar, Callable

Variables = TypeVar('Variables')
Headers = TypeVar('Headers')


class TaskContext(Generic[Variables, Headers]):
    def __init__(self, instance_id: str, workflow_id: str, task_id: str, running_task_id: str, task_type: str,
                 variables: Variables, headers: Headers):
        self.instance_id = instance_id
        self.workflow_id = workflow_id
        self.task_id = task_id
        self.running_task_id = running_task_id
        self.task_type = task_type
        self.variables = variables
        self.headers = headers


TaskDecorator = Callable[[TaskContext], TaskContext]


class BaseDecorator(object):
    def __init__(self, before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        print('Called decorator')
        self._before: List[TaskDecorator] = before or []
        self._after: List[TaskDecorator] = after or []

    def before(self, *decorators: TaskDecorator) -> None:
        self._before.extend(decorators)

    def after(self, *decorators: TaskDecorator) -> None:
        self._after.extend(decorators)
