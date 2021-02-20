import logging
from typing import List, Callable, Dict

from pyzeebe import Job, TaskDecorator
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import DecoratorRunner, JobHandler

logger = logging.getLogger(__name__)


def build_task(task_function: Callable, task_config: TaskConfig) -> Task:
    if not task_config.variables_to_fetch:
        task_config.variables_to_fetch = get_parameters_from_function(task_function)

    if task_config.single_value:
        task_function = convert_to_dict_function(task_function, task_config.variable_name)

    return Task(build_job_handler(task_function, task_config), task_config)


def build_job_handler(task_function: Callable, task_config: TaskConfig) -> JobHandler:
    before_decorator_runner = create_decorator_runner(task_config.before)
    after_decorator_runner = create_decorator_runner(task_config.after)

    def job_handler(job: Job) -> Job:
        try:
            job = before_decorator_runner(job)
            job.variables = task_function(**job.variables)
            job = after_decorator_runner(job)
            job.set_success_status()
        except Exception as e:
            logger.debug(f"Failed job: {job}. Error: {e}.")
            task_config.exception_handler(e, job)
        finally:
            return job

    return job_handler


def create_decorator_runner(decorators: List[TaskDecorator]) -> DecoratorRunner:
    def decorator_runner(job: Job):
        for decorator in decorators:
            job = run_decorator(decorator, job)
        return job

    return decorator_runner


def run_decorator(decorator: TaskDecorator, job: Job) -> Job:
    try:
        return decorator(job)
    except Exception as e:
        logger.warning(f"Failed to run decorator {decorator}. Exception: {e}")
        return job


def convert_to_dict_function(single_value_function: Callable, variable_name: str) -> Callable[..., Dict]:
    def inner_fn(*args, **kwargs):
        return {variable_name: single_value_function(*args, **kwargs)}

    return inner_fn


def get_parameters_from_function(fn: Callable) -> List[str]:
    parameters = fn.__code__.co_varnames
    if "args" in parameters:
        return []
    elif "kwargs" in parameters:
        return []
    else:
        return list(parameters)
