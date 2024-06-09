import logging
from typing import Awaitable, Callable

from pyzeebe.errors.pyzeebe_errors import BusinessError
from pyzeebe.job.job import Job

logger = logging.getLogger(__name__)

ExceptionHandler = Callable[[Exception, Job], Awaitable[None]]


async def default_exception_handler(e: Exception, job: Job) -> None:
    logger.warning("Task type: %s - failed job %s. Error: %s.", job.type, job, e)
    if isinstance(e, BusinessError):
        await job.set_error_status(f"Failed job. Recoverable error: {e}", error_code=e.error_code)
    else:
        await job.set_failure_status(f"Failed job. Error: {e}")
