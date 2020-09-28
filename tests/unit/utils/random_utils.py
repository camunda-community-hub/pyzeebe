from random import randint
from uuid import uuid4

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task

RANDOM_RANGE = 1000000000


def random_job(task: Task = Task(task_type="test", task_handler=lambda x: {"x": x},
                                 exception_handler=lambda x, y, z: x), zeebe_adapter: ZeebeAdapter = None) -> Job:
    return Job(_type=task.type, key=randint(0, RANDOM_RANGE), worker=str(uuid4()),
               retries=randint(0, 10), workflow_instance_key=randint(0, RANDOM_RANGE),
               bpmn_process_id=str(uuid4()), workflow_definition_version=randint(0, 100),
               workflow_key=randint(0, RANDOM_RANGE), element_id=str(uuid4()),
               element_instance_key=randint(0, RANDOM_RANGE), variables={}, custom_headers={},
               deadline=randint(0, RANDOM_RANGE), zeebe_adapter=zeebe_adapter)
