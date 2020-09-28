from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.common.exceptions import TaskNotFound, NoVariableNameGiven
from pyzeebe.task.task import Task
from pyzeebe.worker.task_handler import ZeebeTaskHandler, default_exception_handler
from tests.unit.utils.random_utils import randint, random_job

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


def test_add_dict_task():
    with patch("tests.unit.worker.task_handler_test.zeebe_task_handler._dict_task") as dict_task_mock:
        @zeebe_task_handler.task(task_type=str(uuid4()))
        def dict_task():
            return {}

        dict_task_mock.assert_called()


def test_add_non_dict_task():
    with patch("tests.unit.worker.task_handler_test.zeebe_task_handler._non_dict_task") as non_dict_task_mock:
        @zeebe_task_handler.task(task_type=str(uuid4()), single_value=True, variable_name=str(uuid4()))
        def non_dict_task():
            return True

        non_dict_task_mock.assert_called()


def test_add_non_dict_task_without_variable_name():
    with pytest.raises(NoVariableNameGiven):
        @zeebe_task_handler.task(task_type=str(uuid4()), single_value=True)
        def non_dict_task():
            return True


def test_fn_to_dict():
    variable_name = str(uuid4())

    def no_dict_fn(x):
        return x + 1

    dict_fn = zeebe_task_handler._single_value_function_to_dict(fn=no_dict_fn, variable_name=variable_name)

    variable = randint(0, 1000)
    assert dict_fn(variable) == {variable_name: variable + 1}


def test_default_exception_handler():
    with patch("logging.warning") as logging_mock:
        with patch("pyzeebe.job.job.Job.failure") as failure_mock:
            failure_mock.return_value = None
            job = random_job()
            default_exception_handler(Exception(), job)

            failure_mock.assert_called()
        logging_mock.assert_called()
