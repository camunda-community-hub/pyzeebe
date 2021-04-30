import inspect
import logging
from typing import List, Callable, Dict, Tuple

from pyzeebe import Job, TaskDecorator
from pyzeebe.task.task import Task
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.task.types import DecoratorRunner, JobHandler
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)


def build_task(task_function: Callable, task_config: TaskConfig) -> Task:
    if task_config.single_value:
        task_function = convert_to_dict_function(
            task_function, task_config.variable_name)

    return Task(task_function, build_job_handler(task_function, task_config), task_config)


def build_job_handler(task_function: Callable, task_config: TaskConfig) -> JobHandler:
    before_decorator_runner = create_decorator_runner(task_config.before)
    after_decorator_runner = create_decorator_runner(task_config.after)

    def job_handler(job: Job, task_state: TaskState = None) -> Job:
        if task_state:
            task_state.add(job)
        job = before_decorator_runner(job)
        job.variables, succeeded = run_original_task_function(
            task_function, task_config, job)
        job = after_decorator_runner(job)
        if succeeded:
            job.set_success_status()
        if task_state:
            task_state.remove(job)
        return job

    return job_handler


def run_original_task_function(task_function: Callable, task_config: TaskConfig, job: Job) -> Tuple[Dict, bool]:
    try:
        return task_function(**job.variables), True
    except Exception as e:
        logger.debug(f"Failed job: {job}. Error: {e}.")
        task_config.exception_handler(e, job)
        return job.variables, False


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


def get_parameters_from_function(task_function: Callable) -> List[str]:
    function_signature = inspect.signature(task_function)
    for _, parameter in function_signature.parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            return []
    return list(function_signature.parameters)
