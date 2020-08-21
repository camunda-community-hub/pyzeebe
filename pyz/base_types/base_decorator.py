from typing import List, Callable, Dict


class TaskContext:
    def __init__(self, key: str, _type: str, workflow_instance_key: str, bpmn_process_id: str,
                 workflow_definition_version: int, workflow_key: str, element_id: str, element_instance_key: str,
                 custom_headers: Dict, worker: str, retries: int, deadline: int, variables: Dict):
        self.key = key
        self.type = _type
        self.wokflow_instance_key = workflow_instance_key
        self.bpmn_process_id = bpmn_process_id
        self.workflow_definition_version = workflow_definition_version
        self.workflow_key = workflow_key
        self.element_id = element_id
        self.element_instance_key = element_instance_key
        self.custom_headers = custom_headers
        self.worker = worker
        self.retries = retries
        self.deadline = deadline
        self.variables = variables


TaskDecorator = Callable[[TaskContext], TaskContext]


class BaseDecorator(object):
    def __init__(self, before: List[TaskDecorator] = None, after: List[TaskDecorator] = None):
        self._before: List[TaskDecorator] = before or []
        self._after: List[TaskDecorator] = after or []

    def before(self, *decorators: TaskDecorator) -> None:
        self._before.extend(decorators)

    def after(self, *decorators: TaskDecorator) -> None:
        self._after.extend(decorators)
