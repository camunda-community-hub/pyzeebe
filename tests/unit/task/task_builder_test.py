from typing import Callable, List

import pytest

from pyzeebe import Job, TaskDecorator
from pyzeebe.task import task_builder
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig
from tests.unit.utils import dummy_functions


class TestBuildTask:
    @pytest.fixture
    def single_value_task_config(self, task_config: TaskConfig):
        task_config.single_value = True
        task_config.variable_name = "y"

        return task_config

    def test_returns_task(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_task(original_task_function, task_config)

        assert isinstance(task, Task)

    def test_single_value_func(self, single_value_task_config: TaskConfig, mocked_job_with_adapter: Job):
        task = task_builder.build_task(lambda: 1, single_value_task_config)
        job = task.job_handler(mocked_job_with_adapter)

        assert job.variables.pop("y") == 1

    def test_no_additional_variables_are_added_to_result(self, single_value_task_config: TaskConfig, mocked_job_with_adapter: Job):
        mocked_job_with_adapter.variables = {"x": 1}

        task = task_builder.build_task(lambda x: x, single_value_task_config)
        job = task.job_handler(mocked_job_with_adapter)

        assert len(job.variables.keys()) == 1
        assert set(job.variables.keys()) == {"y"}


class TestBuildJobHandler:
    def test_returned_task_is_callable(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_job_handler(
            original_task_function, task_config)
        assert callable(task)

    def test_exception_handler_called(self, original_task_function: Callable, task_config: TaskConfig,
                                      mocked_job_with_adapter: Job):
        exception = Exception()
        original_task_function.side_effect = exception
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job_handler(mocked_job_with_adapter)

        task_config.exception_handler.assert_called_with(
            exception, mocked_job_with_adapter)

    def test_parameters_are_provided_to_task(self, original_task_function: Callable, task_config: TaskConfig,
                                             mocked_job_with_adapter: Job):
        mocked_job_with_adapter.variables = {"x": 1}
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job_handler(mocked_job_with_adapter)

        original_task_function.assert_called_with(x=1)

    def test_variables_are_added_to_result(self, original_task_function: Callable, task_config: TaskConfig,
                                           mocked_job_with_adapter: Job):
        original_task_function.return_value = {"x": 1}
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job = job_handler(mocked_job_with_adapter)

        assert job.variables.pop("x") == 1

    def test_complete_job_called(self, original_task_function: Callable, task_config: TaskConfig,
                                 mocked_job_with_adapter: Job):
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job_handler(mocked_job_with_adapter)

        mocked_job_with_adapter.set_success_status.assert_called_once()

    def test_returned_task_runs_original_function(self, original_task_function: Callable, task_config: TaskConfig,
                                                  mocked_job_with_adapter: Job):
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job_handler(mocked_job_with_adapter)

        original_task_function.assert_called_once()

    def test_before_decorator_called(self, original_task_function: Callable, decorator: TaskDecorator,
                                     task_config: TaskConfig,
                                     mocked_job_with_adapter: Job):
        task_config.before.append(decorator)
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job_handler(mocked_job_with_adapter)

        task_config.before.pop().assert_called_once()

    def test_after_decorator_called(self, original_task_function: Callable, decorator: TaskDecorator,
                                    task_config: TaskConfig,
                                    mocked_job_with_adapter: Job):
        task_config.after.append(decorator)
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job_handler(mocked_job_with_adapter)

        task_config.after.pop().assert_called_once()

    def test_failing_decorator_continues(self, original_task_function: Callable, decorator: TaskDecorator,
                                         task_config: TaskConfig, mocked_job_with_adapter: Job):
        decorator.side_effect = Exception()
        task_config.before.append(decorator)
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job_handler(mocked_job_with_adapter)

        decorator.assert_called_once()
        task_config.exception_handler.assert_not_called()

    def test_decorator_variables_are_added(self, original_task_function: Callable, decorator: TaskDecorator,
                                           task_config: TaskConfig, mocked_job_with_adapter: Job):
        mocked_job_with_adapter.variables = {"x": 2}
        decorator_return_value = mocked_job_with_adapter
        decorator.return_value = decorator_return_value
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job = job_handler(mocked_job_with_adapter)

        assert "x" in job.variables


class TestConvertToDictFunction:
    def test_converting_to_dict(self):
        dict_function = task_builder.convert_to_dict_function(lambda x: x, "x")

        assert {"x": 1} == dict_function(1)


class TestGetFunctionParameters:
    @pytest.mark.parametrize("fn,expected", [
        (dummy_functions.no_param, []),
        (dummy_functions.one_param, ["x"]),
        (dummy_functions.multiple_params, ["x", "y", "z"]),
        (dummy_functions.one_keyword_param, ["x"]),
        (dummy_functions.multiple_keyword_param, ["x", "y", "z"]),
        (dummy_functions.positional_and_keyword_params, ["x", "y"]),
        (dummy_functions.args_param, []),
        (dummy_functions.kwargs_param, []),
        (dummy_functions.standard_named_params, ["args", "kwargs"]),
        (dummy_functions.lambda_no_params, []),
        (dummy_functions.lambda_one_param, ["x"]),
        (dummy_functions.lambda_multiple_params, ["x", "y", "z"]),
        (dummy_functions.lambda_one_keyword_param, ["x"]),
        (dummy_functions.lambda_multiple_keyword_params, ["x", "y", "z"]),
        (dummy_functions.lambda_positional_and_keyword_params, ["x", "y"])
    ])
    def test_get_params(self, fn: Callable, expected: List[str]):
        assert task_builder.get_parameters_from_function(fn) == expected
