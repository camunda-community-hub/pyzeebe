from threading import Thread
from typing import Dict
from unittest.mock import patch
from uuid import uuid4

from pyzeebe import Task, ZeebeWorker, ZeebeClient


def task_handler(should_throw: bool, input: str) -> Dict:
    if should_throw:
        raise Exception('Error thrown')
    else:
        return {'output': input + str(uuid4())}


def exception_handler(*args, **kwargs):
    pass


task = Task('test', task_handler, exception_handler)

zeebe_client: ZeebeClient
thread: Thread


def setup_module():
    zeebe_worker = ZeebeWorker()
    zeebe_worker.add_task(task)

    thread = Thread(target=zeebe_worker.work)
    thread.start()
    global zeebe_client
    zeebe_client = ZeebeClient()


def teardown_module():
    thread.join()


def test_run_workflow():
    workflow_key = zeebe_client.run_workflow('test', {'input': str(uuid4()), 'should_throw': False})
    assert isinstance(workflow_key, int)


def test_run_workflow_with_result():
    input = str(uuid4())
    output = zeebe_client.run_workflow_with_result('test', {'input': input, 'should_throw': False})
    assert isinstance(output['output'], str)
    assert output['output'].starts_with(input)


def test_cancel_workflow():
    workflow_key = zeebe_client.run_workflow('test', {'input': str(uuid4()), 'should_throw': False})
    zeebe_client.cancel_workflow_instance(workflow_key)


def test_run_error_workflow():
    with patch('tests.exception_handler') as exc_handler:
        zeebe_client.run_workflow('test', {'input': str(uuid4()), 'should_throw': True})
        exc_handler.assert_called()
