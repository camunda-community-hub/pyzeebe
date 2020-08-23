from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.common.random_utils import random_task_context
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.task.task_status_controller import TaskStatusController

task_status_controller: TaskStatusController


@pytest.fixture(autouse=True)
def run_around_tests():
    zeebe_adapter = ZeebeAdapter()
    global task_status_controller
    task_status_controller = TaskStatusController(random_task_context(), zeebe_adapter)
    yield
    task_status_controller = TaskStatusController(random_task_context(), zeebe_adapter)


def test_success():
    with patch('pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job') as complete_job_mock:
        task_status_controller.success()
        complete_job_mock.assert_called_with(job_key=task_status_controller.context.key,
                                             variables=task_status_controller.context.variables)


def test_error():
    with patch('pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.throw_error') as throw_error_mock:
        message = str(uuid4())
        task_status_controller.error(message)
        throw_error_mock.assert_called_with(job_key=task_status_controller.context.key,
                                            message=message)


def test_failure():
    with patch('pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.fail_job') as fail_job_mock:
        message = str(uuid4())
        task_status_controller.failure(message)
        fail_job_mock.assert_called_with(job_key=task_status_controller.context.key,
                                         message=message)
