from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Sequence
from typing import Any, TypeVar

from typing_extensions import ParamSpec

from pyzeebe import Job
from pyzeebe.function_tools import DictFunction, Function
from pyzeebe.function_tools.async_tools import asyncify, is_async_function
from pyzeebe.function_tools.dict_tools import convert_to_dict_function
from pyzeebe.function_tools.parameter_tools import get_job_parameter_name
from pyzeebe.job.job import JobController
from pyzeebe.task.exception_handler import default_exception_handler
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import AsyncTaskDecorator, DecoratorRunner, JobHandler
from pyzeebe.types import Variables

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def build_task(task_function: Function[..., Any], task_config: TaskConfig) -> Task:
    task_config.job_parameter_name = get_job_parameter_name(task_function)
    return Task(task_function, build_job_handler(task_function, task_config), task_config)


def build_job_handler(task_function: Function[..., Any], task_config: TaskConfig) -> JobHandler:
    prepared_task_function = prepare_task_function(task_function, task_config)

    before_decorator_runner = create_decorator_runner(task_config.before)
    after_decorator_runner = create_decorator_runner(task_config.after)

    @functools.wraps(task_function)
    async def job_handler(job: Job, job_controller: JobController) -> Job:
        job = await before_decorator_runner(job)
        return_variables, succeeded = await run_original_task_function(
            prepared_task_function, task_config, job, job_controller
        )
        job.set_task_result(return_variables)
        await job_controller.set_running_after_decorators_status()
        job = await after_decorator_runner(job)
        if succeeded:
            await job_controller.set_success_status(variables=return_variables)
        return job

    return job_handler


def prepare_task_function(task_function: Function[P, R], task_config: TaskConfig) -> DictFunction[P]:
    if not is_async_function(task_function):
        task_function = asyncify(task_function)

    if task_config.single_value:
        return convert_to_dict_function(task_function, task_config.variable_name)
    # we check return type in task decorator
    return task_function  # type: ignore[return-value]


async def run_original_task_function(
    task_function: DictFunction[...], task_config: TaskConfig, job: Job, job_controller: JobController
) -> tuple[Variables, bool]:
    try:
        if task_config.variables_to_fetch is None:
            variables: dict[str, Any] = {}
        elif task_wants_all_variables(task_config):
            if only_job_is_required_in_task_function(task_function):
                variables = {}
            else:
                variables = {**job.variables}
        else:
            variables = {
                k: v
                for k, v in job.variables.items()
                if k in task_config.variables_to_fetch or k == task_config.job_parameter_name
            }

        if task_config.job_parameter_name:
            variables[task_config.job_parameter_name] = job

        returned_value = await task_function(**variables)

        if returned_value is None:
            returned_value = {}

        return returned_value, True
    except Exception as e:
        logger.debug("Failed job: %s. Error: %s.", job, e)
        exception_handler = task_config.exception_handler or default_exception_handler
        await exception_handler(e, job, job_controller)
        return job.variables, False


def only_job_is_required_in_task_function(task_function: DictFunction[...]) -> bool:
    function_signature = inspect.signature(task_function)
    return all(param.annotation == Job for param in function_signature.parameters.values())


def task_wants_all_variables(task_config: TaskConfig) -> bool:
    return task_config.variables_to_fetch == []


def create_decorator_runner(decorators: Sequence[AsyncTaskDecorator]) -> DecoratorRunner:
    async def decorator_runner(job: Job) -> Job:
        for decorator in decorators:
            job = await run_decorator(decorator, job)
        return job

    return decorator_runner


async def run_decorator(decorator: AsyncTaskDecorator, job: Job) -> Job:
    try:
        return await decorator(job)
    except Exception as e:
        logger.warning("Failed to run decorator %s. Exception: %s", decorator, e, exc_info=True)
        return job
