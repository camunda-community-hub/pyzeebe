from collections import Callable

from pyzeebe import Job, TaskDecorator
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.worker.task_builder import build_task


def test_returned_task_is_callable(original_task_function: Callable, task_config: TaskConfig):
    task = build_task(original_task_function, task_config)
    assert callable(task)


def test_exception_handler_called(original_task_function: Callable, task_config: TaskConfig,
                                  mocked_job_with_adapter: Job):
    exception = Exception()
    original_task_function.side_effect = exception

    build_task(original_task_function, task_config)(mocked_job_with_adapter)

    task_config.exception_handler.assert_called_with(exception, mocked_job_with_adapter)


def test_parameters_are_provided_to_task(original_task_function: Callable, task_config: TaskConfig,
                                         mocked_job_with_adapter: Job):
    mocked_job_with_adapter.variables = {"x": 1}

    build_task(original_task_function, task_config)(mocked_job_with_adapter)

    original_task_function.assert_called_with(x=1)


def test_variables_are_added_to_result(original_task_function: Callable, task_config: TaskConfig,
                                       mocked_job_with_adapter: Job):
    original_task_function.return_value = {"x": 1}

    job = build_task(original_task_function, task_config)(mocked_job_with_adapter)

    assert job.variables.pop("x") == 1


def test_complete_job_called(original_task_function: Callable, task_config: TaskConfig, mocked_job_with_adapter: Job):
    build_task(original_task_function, task_config)(mocked_job_with_adapter)
    mocked_job_with_adapter.set_success_status.assert_called_once()


def test_returned_task_runs_original_function(original_task_function: Callable, task_config: TaskConfig,
                                              mocked_job_with_adapter: Job):
    build_task(original_task_function, task_config)(mocked_job_with_adapter)

    original_task_function.assert_called_once()


def test_before_decorator_called(original_task_function: Callable, decorator: TaskDecorator, task_config: TaskConfig,
                                 mocked_job_with_adapter: Job):
    task_config.before.append(decorator)

    build_task(original_task_function, task_config)(mocked_job_with_adapter)

    task_config.before.pop().assert_called_once()


def test_after_decorator_called(original_task_function: Callable, decorator: TaskDecorator, task_config: TaskConfig,
                                mocked_job_with_adapter: Job):
    task_config.after.append(decorator)

    build_task(original_task_function, task_config)(mocked_job_with_adapter)

    task_config.after.pop().assert_called_once()


def test_failing_decorator_continues(original_task_function: Callable, decorator: TaskDecorator,
                                     task_config: TaskConfig, mocked_job_with_adapter: Job):
    decorator.side_effect = Exception()
    task_config.before.append(decorator)

    # Assert no exception is raised
    build_task(original_task_function, task_config)(mocked_job_with_adapter)
    decorator.assert_called_once()
    task_config.exception_handler.assert_not_called()


def test_decorator_variables_are_added(original_task_function: Callable, decorator: TaskDecorator,
                                       task_config: TaskConfig, mocked_job_with_adapter: Job):
    decorator_return_value = mocked_job_with_adapter
    decorator_return_value.variables = {"x": 2}
    decorator.return_value = decorator_return_value

    job = build_task(original_task_function, task_config)(mocked_job_with_adapter)

    assert "x" in job.variables
