import logging
from collections.abc import Awaitable
from typing import Callable

from pyzeebe.errors.pyzeebe_errors import BusinessError
from pyzeebe.job.job import Job, JobController

logger = logging.getLogger(__name__)

ExceptionHandler = Callable[[Exception, Job, JobController], Awaitable[None]]


async def default_exception_handler(e: Exception, job: Job, job_controller: JobController) -> None:
    logger.warning("Task type: %s - failed job %s. Error: %s.", job.type, job, e)
    if isinstance(e, BusinessError):
        await job_controller.set_error_status(f"Failed job. Recoverable error: {e}", error_code=e.error_code)
    else:
        await job_controller.set_failure_status(f"Failed job. Error: {e}")
