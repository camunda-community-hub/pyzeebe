from random import randint
from uuid import uuid4

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job
from pyzeebe.task import task_builder
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig

RANDOM_RANGE = 1000000000


def random_job(task: Task = task_builder.build_task(lambda x: {"x": x}, TaskConfig("test", lambda: None, 10000, 32, 32, [], False, "", [], [])),
               zeebe_adapter: ZeebeAdapter = None) -> Job:
    return Job(_type=task.type, key=randint(0, RANDOM_RANGE), worker=str(uuid4()),
               retries=randint(0, 10), process_instance_key=randint(0, RANDOM_RANGE),
               bpmn_process_id=str(uuid4()), process_definition_version=randint(0, 100),
               process_definition_key=randint(0, RANDOM_RANGE), element_id=str(uuid4()),
               element_instance_key=randint(0, RANDOM_RANGE), variables={}, custom_headers={},
               deadline=randint(0, RANDOM_RANGE), zeebe_adapter=zeebe_adapter)
