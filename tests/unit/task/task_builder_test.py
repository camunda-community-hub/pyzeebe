import copy
from typing import Callable

import pytest

from pyzeebe import Job, JobController, TaskDecorator
from pyzeebe.job.job_status import JobStatus
from pyzeebe.task import task_builder
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig
from tests.unit.utils.random_utils import random_job


class TestBuildTask:
    @pytest.fixture
    def single_value_task_config(self, task_config: TaskConfig):
        task_config.single_value = True
        task_config.variable_name = "y"

        return task_config

    def test_returns_task(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_task(original_task_function, task_config)

        assert isinstance(task, Task)

    @pytest.mark.anyio
    async def test_single_value_func(
        self, single_value_task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        task = task_builder.build_task(lambda: 1, single_value_task_config)
        job = await task.job_handler(job, mocked_job_controller)

        assert job.variables == {}
        mocked_job_controller.set_success_status.assert_awaited_once_with(variables={"y": 1})

    @pytest.mark.anyio
    async def test_no_additional_variables_are_added_to_result(
        self, single_value_task_config: TaskConfig, mocked_job_controller: JobController
    ):
        job = random_job(variables={"x": 1})
        single_value_task_config.variables_to_fetch = ["x"]

        task = task_builder.build_task(lambda x: x, single_value_task_config)
        job = await task.job_handler(job, mocked_job_controller)

        assert len(job.variables.keys()) == 1
        assert set(job.variables.keys()) == {"x"}

        mocked_job_controller.set_success_status.assert_awaited_once_with(variables={"y": 1})

    @pytest.mark.anyio
    async def test_job_parameter_is_injected_in_task(
        self, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        def function_with_job_parameter(job: Job):
            return {"received_job": job}

        task = task_builder.build_task(function_with_job_parameter, task_config)
        job = await task.job_handler(job, mocked_job_controller)

        assert mocked_job_controller.set_success_status.call_args.kwargs["variables"]["received_job"] == job

    @pytest.mark.anyio
    async def test_job_parameter_is_removed_after_job_handler_call(
        self, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        def function_with_job_parameter(job: Job):
            return {"job": job}

        task = task_builder.build_task(function_with_job_parameter, task_config)
        job = await task.job_handler(job, mocked_job_controller)

        assert "job" not in job.variables


class TestBuildJobHandler:
    def test_returned_task_is_callable(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_job_handler(original_task_function, task_config)
        assert callable(task)

    @pytest.mark.anyio
    async def test_exception_handler_called(
        self, original_task_function: Callable, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        exception = Exception()
        original_task_function.side_effect = exception
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        await job_handler(job, mocked_job_controller)

        task_config.exception_handler.assert_called_with(exception, job, mocked_job_controller)

    @pytest.mark.anyio
    async def test_parameters_are_provided_to_task(
        self, original_task_function: Callable, task_config: TaskConfig, mocked_job_controller: JobController
    ):
        job = random_job(variables={"x": 1})
        task_config.variables_to_fetch = ["x"]

        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        await job_handler(job, mocked_job_controller)

        original_task_function.assert_called_with(x=1)

    @pytest.mark.anyio
    async def test_parameters_are_provided_to_task_with_only_job(
        self, original_task_function: Callable, task_config: TaskConfig, mocked_job_controller: JobController
    ):
        task_with_only_job_called = False

        def task_with_only_job(job: Job):
            nonlocal task_with_only_job_called
            task_with_only_job_called = True

        job = random_job(variables={"x": 1})
        task_config.job_parameter_name = "job"
        task_config.variables_to_fetch = []

        job_handler = task_builder.build_job_handler(task_with_only_job, task_config)

        await job_handler(job, mocked_job_controller)

        assert task_with_only_job_called, "Task was called ok"

    @pytest.mark.anyio
    async def test_parameters_are_provided_to_task_with_arg_and_job(
        self, task_config: TaskConfig, mocked_job_controller: JobController
    ):
        call_params = None

        def task_with_arg_and_job(job: Job, x):
            nonlocal call_params
            call_params = {"job": job, "x": x}

        job = random_job(variables={"x": 1})
        task_config.job_parameter_name = "job"
        task_config.variables_to_fetch = ["x"]

        job_handler = task_builder.build_job_handler(task_with_arg_and_job, task_config)

        await job_handler(job, mocked_job_controller)

        assert call_params == {"job": job, "x": 1}

    @pytest.mark.anyio
    async def test_variables_are_added_to_result(
        self, original_task_function: Callable, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        original_task_function.return_value = {"x": 1}
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        job = await job_handler(job, mocked_job_controller)

        assert job.variables == {}
        mocked_job_controller.set_success_status.assert_awaited_once_with(variables={"x": 1})

    @pytest.mark.anyio
    async def test_job_variables_are_not_overridden(
        self, original_task_function: Callable, task_config: TaskConfig, mocked_job_controller: JobController
    ):
        job = random_job(variables={"x": 1})
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        job = await job_handler(job, mocked_job_controller)

        assert job.variables.pop("x") == 1

    @pytest.mark.anyio
    async def test_complete_job_called(
        self, original_task_function: Callable, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        await job_handler(job, mocked_job_controller)

        mocked_job_controller.set_success_status.assert_called_once_with(variables={})

    @pytest.mark.anyio
    async def test_returned_task_runs_original_function(
        self, original_task_function: Callable, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        await job_handler(job, mocked_job_controller)

        original_task_function.assert_called_once()

    @pytest.mark.anyio
    async def test_empty_variables_to_fetch_results_in_all_vars_passed_to_task(
        self, mocked_job_controller: JobController, task_config: TaskConfig
    ):
        task_config.variables_to_fetch = []
        task_config.job_parameter_name = "job"

        call_params = None

        def task_with_params(job: Job, *args, **kwargs):
            nonlocal call_params
            call_params = {"job": job, "args": args, "kwargs": kwargs}

        job = random_job(variables={"a": 1, "b": 2})

        job_handler = task_builder.build_job_handler(task_with_params, task_config)

        await job_handler(job, mocked_job_controller)

        assert call_params == {"job": job, "args": (), "kwargs": {"a": 1, "b": 2}}

    @pytest.mark.anyio
    async def test_before_decorator_called(
        self,
        original_task_function: Callable,
        decorator: TaskDecorator,
        task_config: TaskConfig,
        job: Job,
        mocked_job_controller: JobController,
    ):
        task_config.before.append(decorator)
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        await job_handler(job, mocked_job_controller)

        task_config.before.pop().assert_called_once()

    @pytest.mark.anyio
    async def test_after_decorator_called(
        self,
        original_task_function: Callable,
        decorator: TaskDecorator,
        task_config: TaskConfig,
        job: Job,
        mocked_job_controller: JobController,
    ):
        task_config.after.append(decorator)
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        await job_handler(job, mocked_job_controller)

        task_config.after.pop().assert_called_once()

    @pytest.mark.anyio
    async def test_after_decorator_can_access_task_result(
        self,
        task_config: TaskConfig,
        job: Job,
        mocked_job_controller: JobController,
    ):
        async def task_function():
            return {"result": 1}

        task_result = dict()

        async def after_decorator(job: Job):
            nonlocal task_result
            task_result = job.task_result
            return job

        task_config.after.append(after_decorator)
        job_handler = task_builder.build_job_handler(task_function, task_config)

        await job_handler(job, mocked_job_controller)

        assert task_result == {"result": 1}

    @pytest.mark.anyio
    async def test_failing_decorator_continues(
        self,
        original_task_function: Callable,
        decorator: TaskDecorator,
        task_config: TaskConfig,
        job: Job,
        mocked_job_controller: JobController,
    ):
        decorator.side_effect = Exception()
        task_config.before.append(decorator)
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        await job_handler(job, mocked_job_controller)

        decorator.assert_called_once()
        task_config.exception_handler.assert_not_called()

    @pytest.mark.anyio
    async def test_decorator_variables_are_added(
        self,
        original_task_function: Callable,
        decorator: TaskDecorator,
        task_config: TaskConfig,
        mocked_job_controller: JobController,
    ):
        job = random_job(variables={"x": 2})
        decorator_return_value = job
        decorator.return_value = decorator_return_value
        job_handler = task_builder.build_job_handler(original_task_function, task_config)

        job = await job_handler(job, mocked_job_controller)

        assert "x" in job.variables

    @pytest.mark.anyio
    async def test_job_status_is_updated(
        self,
        task_config: TaskConfig,
        job: Job,
        job_controller: JobController,
    ):
        job_handler = task_builder.build_job_handler(self.function_with_job_parameter, task_config)
        job = await job_handler(job, job_controller)

        assert job.status == JobStatus.RunningAfterDecorators

    @pytest.mark.anyio
    async def test_job_parameter_is_injected(
        self, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        task_config.job_parameter_name = "job"

        job_handler = task_builder.build_job_handler(self.function_with_job_parameter, task_config)
        job = await job_handler(job, mocked_job_controller)

        assert mocked_job_controller.set_success_status.call_args.kwargs["variables"]["received_job"] == job

    @pytest.mark.anyio
    async def test_job_parameter_retains_variables(
        self, task_config: TaskConfig, job: Job, mocked_job_controller: JobController
    ):
        task_config.job_parameter_name = "job"
        expected_variables = copy.copy(job.variables)

        job_handler = task_builder.build_job_handler(self.function_with_job_parameter, task_config)
        job = await job_handler(job, mocked_job_controller)

        assert (
            mocked_job_controller.set_success_status.call_args.kwargs["variables"]["received_job"].variables
            == expected_variables
        )

    def function_with_job_parameter(x: int, job: Job):
        return {"received_job": job}
