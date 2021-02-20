import logging
from typing import List, Callable

from pyzeebe import Job, TaskDecorator
from pyzeebe.task.task_config import TaskConfig

logger = logging.getLogger(__name__)
DecoratorRunner = Callable[[Job], Job]
JobHandler = Callable[[Job], Job]


def build_task(task_function, task_config: TaskConfig) -> JobHandler:
    before_decorator_runner = create_decorator_runner(task_config.before)
    after_decorator_runner = create_decorator_runner(task_config.after)

    def job_handler(job: Job) -> Job:
        try:
            job = before_decorator_runner(job)
            job.variables = task_function(**job.variables)
            job = after_decorator_runner(job)
            job.set_success_status()
        except Exception as e:
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
