from uuid import uuid4

import pytest

from pyzeebe.common.exceptions import TaskNotFound
from pyzeebe.task.task import Task
from pyzeebe.worker.task_handler import ZeebeTaskHandler
from tests.unit.utils.random_utils import randint

zeebe_task_handler: ZeebeTaskHandler
task: Task


@pytest.fixture(autouse=True)
def run_around_tests():
    global zeebe_task_handler, task
    task = Task(str(uuid4()), lambda x: {"x": x}, lambda x, y, z: x)
    zeebe_task_handler = ZeebeTaskHandler()
    yield
    zeebe_task_handler = ZeebeTaskHandler()
    task = Task(str(uuid4()), lambda x: {"x": x}, lambda x, y, z: x)


def test_get_task():
    zeebe_task_handler.tasks.append(task)
    found_task = zeebe_task_handler.get_task(task.type)
    assert isinstance(found_task, Task)
    assert found_task == task


def test_get_fake_task():
    with pytest.raises(TaskNotFound):
        zeebe_task_handler.get_task(str(uuid4()))


def test_get_task_index():
    zeebe_task_handler.tasks.append(task)
    index = zeebe_task_handler._get_task_index(task.type)
    assert isinstance(index, int)
    assert zeebe_task_handler.tasks[index] == task


def test_get_task_and_index():
    zeebe_task_handler.tasks.append(task)
    found_task, index = zeebe_task_handler._get_task_and_index(task.type)
    assert isinstance(index, int)
    assert zeebe_task_handler.tasks[index] == task
    assert isinstance(found_task, Task)
    assert found_task == task


def test_remove_task():
    zeebe_task_handler.tasks.append(task)
    assert zeebe_task_handler.remove_task(task.type) is not None
    assert task not in zeebe_task_handler.tasks


def test_remove_task_from_many():
    zeebe_task_handler.tasks.append(task)

    for i in range(0, randint(0, 100)):
        zeebe_task_handler.tasks.append(Task(str(uuid4()), lambda x: x, lambda x: x))
    assert zeebe_task_handler.remove_task(task.type) is not None
    assert task not in zeebe_task_handler.tasks


def test_remove_fake_task():
    with pytest.raises(TaskNotFound):
        zeebe_task_handler.remove_task(str(uuid4()))
