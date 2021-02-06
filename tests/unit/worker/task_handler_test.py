from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from pyzeebe.exceptions import NoVariableNameGiven, TaskNotFound, DuplicateTaskType
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
        task_handler.tasks.append(Task(str(uuid4()), lambda x: x, lambda x: x))
    assert task_handler.remove_task(task.type) is not None
    assert task not in task_handler.tasks


def test_remove_fake_task(task_handler):
    with pytest.raises(TaskNotFound):
        task_handler.remove_task(str(uuid4()))


def test_add_dict_task(task_handler):
    task_handler._dict_task = MagicMock()

    @task_handler.task(task_type=str(uuid4()))
    def dict_task():
        return {}

    task_handler._dict_task.assert_called()


def test_add_non_dict_task(task_handler):
    task_handler._non_dict_task = MagicMock()

    @task_handler.task(task_type=str(uuid4()), single_value=True, variable_name=str(uuid4()))
    def non_dict_task():
        return True

    task_handler._non_dict_task.assert_called()


def test_add_non_dict_task_without_variable_name(task_handler):
    with pytest.raises(NoVariableNameGiven):
        @task_handler.task(task_type=str(uuid4()), single_value=True)
        def non_dict_task():
            return True


def test_fn_to_dict(task_handler):
    variable_name = str(uuid4())

    def no_dict_fn(x):
        return x + 1

    dict_fn = task_handler._single_value_function_to_dict(fn=no_dict_fn, variable_name=variable_name)

    variable = randint(0, 1000)
    assert dict_fn(variable) == {variable_name: variable + 1}


def test_default_exception_handler(job_without_adapter):
    with patch("pyzeebe.worker.task_handler.logger.warning") as logging_mock:
        with patch("pyzeebe.job.job.Job.set_failure_status") as failure_mock:
            failure_mock.return_value = None
            default_exception_handler(Exception(), job_without_adapter)

            failure_mock.assert_called()
        logging_mock.assert_called()


def test_get_parameters_from_function_no_parameters(task_handler):
    def no_parameters():
        pass

    assert task_handler._get_parameters_from_function(no_parameters) == []


def test_get_parameters_from_function_one_positional(task_handler):
    def one_pos_func(x):
        pass

    assert task_handler._get_parameters_from_function(one_pos_func) == ["x"]


def test_get_parameters_from_function_multiple_positional(task_handler):
    def mul_pos_func(x, y, z):
        pass

    assert task_handler._get_parameters_from_function(mul_pos_func) == ["x", "y", "z"]


def test_get_parameters_from_function_one_keyword(task_handler):
    def one_key_func(x=0):
        pass

    assert task_handler._get_parameters_from_function(one_key_func) == ["x"]


def test_get_parameters_from_function_multiple_keywords(task_handler):
    def mul_key_func(x=0, y=0, z=0):
        pass

    assert task_handler._get_parameters_from_function(mul_key_func) == ["x", "y", "z"]


def test_get_parameters_from_function_positional_and_keyword(task_handler):
    def pos_and_key_func(x, y=0):
        pass

    assert task_handler._get_parameters_from_function(pos_and_key_func) == ["x", "y"]


def test_get_parameters_from_function_args(task_handler):
    def args_func(*args):
        pass

    assert task_handler._get_parameters_from_function(args_func) == []


def test_get_parameters_from_function_kwargs(task_handler):
    def kwargs_func(**kwargs):
        pass

    assert task_handler._get_parameters_from_function(kwargs_func) == []


def test_get_parameters_from_function_lambda(task_handler):
    my_func = lambda x: x

    assert task_handler._get_parameters_from_function(my_func) == ["x"]


def test_check_is_task_duplicate_with_duplicate(task_handler, task):
    task_handler.tasks.append(task)
    with pytest.raises(DuplicateTaskType):
        task_handler._is_task_duplicate(task.type)


def test_check_is_task_duplicate_no_duplicate(task_handler, task):
    task_handler.tasks.append(task)
