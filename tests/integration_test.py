from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from uuid import uuid4

import pytest

from pyzeebe import Task, ZeebeWorker, ZeebeClient, exceptions, TaskContext, TaskStatusController


def task_handler(should_throw: bool, input: str) -> Dict:
    if should_throw:
        raise Exception('Error thrown')
    else:
        return {'output': input + str(uuid4())}


def exception_handler(exc: Exception, context: TaskContext, controller: TaskStatusController) -> None:
    controller.error(f'Failed to run task {context.type}. Reason: {exc}')


task = Task('test', task_handler, exception_handler)

zeebe_client: ZeebeClient
executor: ThreadPoolExecutor


def run_worker():
    zeebe_worker = ZeebeWorker()
    zeebe_worker.add_task(task)
    zeebe_worker.work()


@pytest.fixture(scope='module', autouse=True)
def setup():
    global p, zeebe_client, executor

    executor = ThreadPoolExecutor()
    executor.submit(run_worker)

    zeebe_client = ZeebeClient()
    zeebe_client.deploy_workflow('test.bpmn')

    yield zeebe_client

    executor.shutdown(wait=False)


def test_run_workflow():
    workflow_key = zeebe_client.run_workflow('test', {'input': str(uuid4()), 'should_throw': False})
    assert isinstance(workflow_key, int)


def test_non_existent_workflow():
    with pytest.raises(exceptions.WorkflowNotFound):
        zeebe_client.run_workflow(str(uuid4()))


def test_run_workflow_with_result():
    input = str(uuid4())
    output = zeebe_client.run_workflow_with_result('test', {'input': input, 'should_throw': False})
    assert isinstance(output['output'], str)
    assert output['output'].startswith(input)


def test_cancel_workflow():
    workflow_key = zeebe_client.run_workflow('test', {'input': str(uuid4()), 'should_throw': False})
    zeebe_client.cancel_workflow_instance(workflow_key)