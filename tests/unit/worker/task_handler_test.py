from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.exceptions import TaskNotFound, DuplicateTaskType
from pyzeebe.task.task import Task
from pyzeebe.worker.task_handler import default_exception_handler
from tests.unit.utils.random_utils import randint


def test_get_task(task_handler, task):
    task_handler.tasks.append(task)
    found_task = task_handler.get_task(task.type)
    assert isinstance(found_task, Task)
    assert found_task == task


def test_get_fake_task(task_handler):
    with pytest.raises(TaskNotFound):
        task_handler.get_task(str(uuid4()))


def test_get_task_index(task_handler, task):
    task_handler.tasks.append(task)
    index = task_handler._get_task_index(task.type)
    assert isinstance(index, int)
    assert task_handler.tasks[index] == task


def test_get_task_and_index(task_handler, task):
    task_handler.tasks.append(task)
    found_task, index = task_handler._get_task_and_index(task.type)
    assert isinstance(index, int)
    assert task_handler.tasks[index] == task
    assert isinstance(found_task, Task)
    assert found_task == task


def test_remove_task(task_handler, task):
    task_handler.tasks.append(task)
    assert task_handler.remove_task(task.type) is not None
    assert task not in task_handler.tasks


def test_remove_task_from_many(task_handler, task):
    task_handler.tasks.append(task)

    for i in range(0, randint(0, 100)):
        @task_handler.task(str(uuid4()))
        def dummy_function():
            pass
    assert task_handler.remove_task(task.type) is not None
    assert task not in task_handler.tasks


def test_remove_fake_task(task_handler):
    with pytest.raises(TaskNotFound):
        task_handler.remove_task(str(uuid4()))


def test_default_exception_handler(job_without_adapter):
    with patch("pyzeebe.worker.task_handler.logger.warning") as logging_mock:
        with patch("pyzeebe.job.job.Job.set_failure_status") as failure_mock:
            failure_mock.return_value = None
            default_exception_handler(Exception(), job_without_adapter)

            failure_mock.assert_called()
        logging_mock.assert_called()


def test_check_is_task_duplicate_with_duplicate(task_handler, task):
    task_handler.tasks.append(task)
    with pytest.raises(DuplicateTaskType):
        task_handler._is_task_duplicate(task.type)


def test_check_is_task_duplicate_no_duplicate(task_handler, task):
    task_handler.tasks.append(task)
