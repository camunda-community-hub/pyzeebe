from dataclasses import dataclass
from typing import Dict

from pyzeebe.task.task_status import TaskStatus


@dataclass
class TaskContext(object):
    key: int
    type: str
    workflow_instance_key: int
    bpmn_process_id: str
    workflow_definition_version: int
    workflow_key: int
    element_id: str
    element_instance_key: int
    custom_headers: Dict
    worker: str
    retries: int
    deadline: int
    variables: Dict
    status: TaskStatus = TaskStatus.Running
