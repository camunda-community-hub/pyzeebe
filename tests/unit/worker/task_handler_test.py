from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.exceptions import NoVariableNameGiven, TaskNotFound, DuplicateTaskType
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
    with patch("pyzeebe.worker.task_handler.logger.warning") as logging_mock:
        with patch("pyzeebe.job.job.Job.set_failure_status") as failure_mock:
            failure_mock.return_value = None
            job = random_job()
            default_exception_handler(Exception(), job)

            failure_mock.assert_called()
        logging_mock.assert_called()


def test_get_parameters_from_function_no_parameters():
    def no_parameters():
        pass

    assert zeebe_task_handler._get_parameters_from_function(no_parameters) == []


def test_get_parameters_from_function_one_positional():
    def one_pos_func(x):
        pass

    assert zeebe_task_handler._get_parameters_from_function(one_pos_func) == ["x"]


def test_get_parameters_from_function_multiple_positional():
    def mul_pos_func(x, y, z):
        pass

    assert zeebe_task_handler._get_parameters_from_function(mul_pos_func) == ["x", "y", "z"]


def test_get_parameters_from_function_one_keyword():
    def one_key_func(x=0):
        pass

    assert zeebe_task_handler._get_parameters_from_function(one_key_func) == ["x"]


def test_get_parameters_from_function_multiple_keywords():
    def mul_key_func(x=0, y=0, z=0):
        pass

    assert zeebe_task_handler._get_parameters_from_function(mul_key_func) == ["x", "y", "z"]


def test_get_parameters_from_function_positional_and_keyword():
    def pos_and_key_func(x, y=0):
        pass

    assert zeebe_task_handler._get_parameters_from_function(pos_and_key_func) == ["x", "y"]


def test_get_parameters_from_function_args():
    def args_func(*args):
        pass

    assert zeebe_task_handler._get_parameters_from_function(args_func) == []


def test_get_parameters_from_function_kwargs():
    def kwargs_func(**kwargs):
        pass

    assert zeebe_task_handler._get_parameters_from_function(kwargs_func) == []


def test_get_parameters_from_function_lambda():
    my_func = lambda x: x

    assert zeebe_task_handler._get_parameters_from_function(my_func) == ["x"]


def test_check_is_task_duplicate_with_duplicate():
    zeebe_task_handler.tasks.append(task)
    with pytest.raises(DuplicateTaskType):
        zeebe_task_handler._is_task_duplicate(task.type)


def test_check_is_task_duplicate_no_duplicate():
    zeebe_task_handler.tasks.append(task)
