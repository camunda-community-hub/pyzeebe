from collections import Callable

from pyzeebe import Job, TaskDecorator
from pyzeebe.task import task_builder
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig


class TestBuildTask:
    def test_returns_task(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_task(original_task_function, task_config)

        assert isinstance(task, Task)

    def test_single_value_func(self, task_config: TaskConfig, mocked_job_with_adapter: Job):
        task_config.single_value = True
        task_config.variable_name = "y"
        mocked_job_with_adapter.variables = {"x": 1}

        job = task_builder.build_task(lambda x: x, task_config).job_handler(mocked_job_with_adapter)

        assert job.variables.pop("y") == 1

    def test_variables_to_fetch_added_to_task_config(self, task_config: TaskConfig):
        expected_variables_to_fetch = ["x", "y"]

        def dummy_fn(x, y):
            pass

        task = task_builder.build_task(dummy_fn, task_config)

        assert task.config.variables_to_fetch == expected_variables_to_fetch


class TestBuildJobHandler:
    def test_returned_task_is_callable(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_job_handler(original_task_function, task_config)
        assert callable(task)

    def test_exception_handler_called(self, original_task_function: Callable, task_config: TaskConfig,
                                      mocked_job_with_adapter: Job):
        exception = Exception()
        original_task_function.side_effect = exception

        task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)

        task_config.exception_handler.assert_called_with(exception, mocked_job_with_adapter)

    def test_parameters_are_provided_to_task(self, original_task_function: Callable, task_config: TaskConfig,
                                             mocked_job_with_adapter: Job):
        mocked_job_with_adapter.variables = {"x": 1}

        task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)

        original_task_function.assert_called_with(x=1)

    def test_variables_are_added_to_result(self, original_task_function: Callable, task_config: TaskConfig,
                                           mocked_job_with_adapter: Job):
        original_task_function.return_value = {"x": 1}

        job = task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)

        assert job.variables.pop("x") == 1

    def test_complete_job_called(self, original_task_function: Callable, task_config: TaskConfig,
                                 mocked_job_with_adapter: Job):
        task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)
        mocked_job_with_adapter.set_success_status.assert_called_once()

    def test_returned_task_runs_original_function(self, original_task_function: Callable, task_config: TaskConfig,
                                                  mocked_job_with_adapter: Job):
        task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)

        original_task_function.assert_called_once()

    def test_before_decorator_called(self, original_task_function: Callable, decorator: TaskDecorator,
                                     task_config: TaskConfig,
                                     mocked_job_with_adapter: Job):
        task_config.before.append(decorator)

        task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)

        task_config.before.pop().assert_called_once()

    def test_after_decorator_called(self, original_task_function: Callable, decorator: TaskDecorator,
                                    task_config: TaskConfig,
                                    mocked_job_with_adapter: Job):
        task_config.after.append(decorator)

        task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)

        task_config.after.pop().assert_called_once()

    def test_failing_decorator_continues(self, original_task_function: Callable, decorator: TaskDecorator,
                                         task_config: TaskConfig, mocked_job_with_adapter: Job):
        decorator.side_effect = Exception()
        task_config.before.append(decorator)

        # Assert no exception is raised
        task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)
        decorator.assert_called_once()
        task_config.exception_handler.assert_not_called()

    def test_decorator_variables_are_added(self, original_task_function: Callable, decorator: TaskDecorator,
                                           task_config: TaskConfig, mocked_job_with_adapter: Job):
        decorator_return_value = mocked_job_with_adapter
        decorator_return_value.variables = {"x": 2}
        decorator.return_value = decorator_return_value

        job = task_builder.build_job_handler(original_task_function, task_config)(mocked_job_with_adapter)

        assert "x" in job.variables


class TestConvertToDictFunction:
    def test_converting_to_dict(self):
        dict_function = task_builder.convert_to_dict_function(lambda x: x, "x")

        assert {"x": 1} == dict_function(1)


class TestGetFunctionParameters:
    def test_get_no_param(self):
        def no_parameters():
            pass

        assert task_builder.get_parameters_from_function(no_parameters) == []

    def test_get_single_param(self):
        def dummy_function(x):
            pass

        assert task_builder.get_parameters_from_function(dummy_function) == ["x"]

    def test_get_multiple_params(self):
        def dummy_function(x, y, z):
            pass

        assert task_builder.get_parameters_from_function(dummy_function) == ["x", "y", "z"]

    def test_get_param_from_lambda(self):
        assert task_builder.get_parameters_from_function(lambda x: None) == ["x"]

    def test_get_one_positional_param(self):
        def one_pos_func(x):
            pass

        assert task_builder.get_parameters_from_function(one_pos_func) == ["x"]

    def test_get_multiple_positional_params(self):
        def mul_pos_func(x, y, z):
            pass

        assert task_builder.get_parameters_from_function(mul_pos_func) == ["x", "y", "z"]

    def test_get_one_keyword_param(self):
        def one_key_func(x=0):
            pass

        assert task_builder.get_parameters_from_function(one_key_func) == ["x"]

    def test_get_multiple_keyword_params(self):
        def mul_key_func(x=0, y=0, z=0):
            pass

        assert task_builder.get_parameters_from_function(mul_key_func) == ["x", "y", "z"]

    def test_get_positional_and_keyword_params(self):
        def pos_and_key_func(x, y=0):
            pass

        assert task_builder.get_parameters_from_function(pos_and_key_func) == ["x", "y"]

    def test_get_params_from_args(self):
        def args_func(*args):
            pass

        assert task_builder.get_parameters_from_function(args_func) == []

    def test_get_params_from_kwargs(self):
        def kwargs_func(**kwargs):
            pass

        assert task_builder.get_parameters_from_function(kwargs_func) == []