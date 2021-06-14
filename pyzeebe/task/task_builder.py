import functools
import logging
from typing import Awaitable, Callable, Dict, Sequence, Tuple

from pyzeebe import Job
from pyzeebe.function_tools.async_tools import asyncify, is_async_function
from pyzeebe.function_tools.dict_tools import convert_to_dict_function
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import AsyncTaskDecorator, DecoratorRunner, JobHandler

logger = logging.getLogger(__name__)


def build_task(task_function: Callable, task_config: TaskConfig) -> Task:
    return Task(task_function, build_job_handler(task_function, task_config), task_config)


def build_job_handler(task_function: Callable, task_config: TaskConfig) -> JobHandler:
    prepared_task_function = prepare_task_function(task_function, task_config)

    before_decorator_runner = create_decorator_runner(task_config.before)
    after_decorator_runner = create_decorator_runner(task_config.after)

    @functools.wraps(task_function)
    async def job_handler(job: Job) -> Job:
        job = await before_decorator_runner(job)
        job.variables, succeeded = await run_original_task_function(
            prepared_task_function, task_config, job
        )
        job = await after_decorator_runner(job)
        if succeeded:
            await job.set_success_status()
        return job

    return job_handler


def prepare_task_function(task_function: Callable, task_config: TaskConfig) -> Callable[..., Awaitable[Dict]]:
    if not is_async_function(task_function):
        task_function = asyncify(task_function)

    if task_config.single_value:
        task_function = convert_to_dict_function(
            task_function, task_config.variable_name
        )
    return task_function


async def run_original_task_function(task_function: Callable, task_config: TaskConfig, job: Job) -> Tuple[Dict, bool]:
    try:
        return await task_function(**job.variables), True
    except Exception as e:
        logger.debug(f"Failed job: {job}. Error: {e}.")
        await task_config.exception_handler(e, job)
        return job.variables, False


def create_decorator_runner(decorators: Sequence[AsyncTaskDecorator]) -> DecoratorRunner:
    async def decorator_runner(job: Job):
        for decorator in decorators:
            job = await run_decorator(decorator, job)
        return job

    return decorator_runner


async def run_decorator(decorator: AsyncTaskDecorator, job: Job) -> Job:
    try:
        return await decorator(job)
    except Exception as e:
        logger.warning(f"Failed to run decorator {decorator}. Exception: {e}")
        return job
