import copy
from typing import Callable

import pytest

from pyzeebe import Job, TaskDecorator
from pyzeebe.task import task_builder
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig


class TestBuildTask:
    @pytest.fixture
    def single_value_task_config(self, task_config: TaskConfig):
        task_config.single_value = True
        task_config.variable_name = "y"

        return task_config

    def test_returns_task(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_task(original_task_function, task_config)

        assert isinstance(task, Task)

    @pytest.mark.asyncio
    async def test_single_value_func(self, single_value_task_config: TaskConfig, mocked_job_with_adapter: Job):
        task = task_builder.build_task(lambda: 1, single_value_task_config)
        job = await task.job_handler(mocked_job_with_adapter)

        assert job.variables.pop("y") == 1

    @pytest.mark.asyncio
    async def test_no_additional_variables_are_added_to_result(self, single_value_task_config: TaskConfig, mocked_job_with_adapter: Job):
        mocked_job_with_adapter.variables = {"x": 1}

        task = task_builder.build_task(lambda x: x, single_value_task_config)
        job = await task.job_handler(mocked_job_with_adapter)

        assert len(job.variables.keys()) == 1
        assert set(job.variables.keys()) == {"y"}

    @pytest.mark.asyncio
    async def test_job_parameter_is_injected_in_task(self, task_config: TaskConfig, mocked_job_with_adapter: Job):
        def function_with_job_parameter(job: Job):
            return {"job": job}

        task = task_builder.build_task(
            function_with_job_parameter, task_config)
        job = await task.job_handler(mocked_job_with_adapter)

        assert job.variables["job"] == mocked_job_with_adapter


class TestBuildJobHandler:
    def test_returned_task_is_callable(self, original_task_function: Callable, task_config: TaskConfig):
        task = task_builder.build_job_handler(
            original_task_function, task_config)
        assert callable(task)

    @pytest.mark.asyncio
    async def test_exception_handler_called(self, original_task_function: Callable, task_config: TaskConfig,
                                            mocked_job_with_adapter: Job):
        exception = Exception()
        original_task_function.side_effect = exception
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        await job_handler(mocked_job_with_adapter)

        task_config.exception_handler.assert_called_with(
            exception, mocked_job_with_adapter)

    @pytest.mark.asyncio
    async def test_parameters_are_provided_to_task(self, original_task_function: Callable, task_config: TaskConfig,
                                                   mocked_job_with_adapter: Job):
        mocked_job_with_adapter.variables = {"x": 1}
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        await job_handler(mocked_job_with_adapter)

        original_task_function.assert_called_with(x=1)

    @pytest.mark.asyncio
    async def test_variables_are_added_to_result(self, original_task_function: Callable, task_config: TaskConfig,
                                                 mocked_job_with_adapter: Job):
        original_task_function.return_value = {"x": 1}
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config
        )

        job = await job_handler(mocked_job_with_adapter)

        assert job.variables.pop("x") == 1

    @pytest.mark.asyncio
    async def test_complete_job_called(self, original_task_function: Callable, task_config: TaskConfig,
                                       mocked_job_with_adapter: Job):
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        await job_handler(mocked_job_with_adapter)

        mocked_job_with_adapter.set_success_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_returned_task_runs_original_function(self, original_task_function: Callable, task_config: TaskConfig,
                                                        mocked_job_with_adapter: Job):
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        await job_handler(mocked_job_with_adapter)

        original_task_function.assert_called_once()

    @pytest.mark.asyncio
    async def test_before_decorator_called(self, original_task_function: Callable, decorator: TaskDecorator,
                                           task_config: TaskConfig,
                                           mocked_job_with_adapter: Job):
        task_config.before.append(decorator)
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config
        )

        await job_handler(mocked_job_with_adapter)

        task_config.before.pop().assert_called_once()

    @pytest.mark.asyncio
    async def test_after_decorator_called(self, original_task_function: Callable, decorator: TaskDecorator,
                                          task_config: TaskConfig,
                                          mocked_job_with_adapter: Job):
        task_config.after.append(decorator)
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config
        )

        await job_handler(mocked_job_with_adapter)

        task_config.after.pop().assert_called_once()

    @pytest.mark.asyncio
    async def test_failing_decorator_continues(self, original_task_function: Callable, decorator: TaskDecorator,
                                               task_config: TaskConfig, mocked_job_with_adapter: Job):
        decorator.side_effect = Exception()
        task_config.before.append(decorator)
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config
        )

        await job_handler(mocked_job_with_adapter)

        decorator.assert_called_once()
        task_config.exception_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_decorator_variables_are_added(self, original_task_function: Callable, decorator: TaskDecorator,
                                                 task_config: TaskConfig, mocked_job_with_adapter: Job):
        mocked_job_with_adapter.variables = {"x": 2}
        decorator_return_value = mocked_job_with_adapter
        decorator.return_value = decorator_return_value
        job_handler = task_builder.build_job_handler(
            original_task_function, task_config)

        job = await job_handler(mocked_job_with_adapter)

        assert "x" in job.variables

    @pytest.mark.asyncio
    async def test_job_parameter_is_injected(self, task_config: TaskConfig, mocked_job_with_adapter: Job):
        task_config.job_parameter_name = "job"

        job_handler = task_builder.build_job_handler(
            self.function_with_job_parameter, task_config
        )
        job = await job_handler(mocked_job_with_adapter)

        assert job.variables["job"] == mocked_job_with_adapter

    @pytest.mark.asyncio
    async def test_job_parameter_retains_variables(self, task_config: TaskConfig, mocked_job_with_adapter: Job):
        task_config.job_parameter_name = "job"
        expected_variables = copy.copy(mocked_job_with_adapter.variables)

        job_handler = task_builder.build_job_handler(
            self.function_with_job_parameter, task_config
        )
        job = await job_handler(mocked_job_with_adapter)

        assert job.variables["job"].variables == expected_variables

    def function_with_job_parameter(x: int, job: Job):
        return {"job": job}

