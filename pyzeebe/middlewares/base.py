from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, final

from pyzeebe.errors import BusinessError
from pyzeebe.types import MiddlewareProto

if TYPE_CHECKING:
    from pyzeebe.job.job import Job, JobController
    from pyzeebe.task.task import Task
    from pyzeebe.types import ExceptionHandler, JobHandler

logger = logging.getLogger(__name__)


class Middleware:
    def __init__(self, cls: type[MiddlewareProto], **options: Any) -> None:
        self.cls = cls
        self.options = options


@final
class CatchErrorMiddleware(MiddlewareProto):
    async def __call__(self, job: Job, job_controller: JobController, *, task: Task, call_next: JobHandler) -> None:
        try:
            await call_next(job, job_controller)
        except BusinessError:
            raise
        except Exception as err:
            logger.debug("Failed job: %s. Error: %s.", job, err, exc_info=err)
            raise
        finally:
            await job_controller.set_running_after_decorators_status()


@final
class ResponseMiddleware(MiddlewareProto):
    def __init__(self, exception_handlers: Mapping[type[Exception], ExceptionHandler]) -> None:
        self.exception_handlers = exception_handlers

    async def __call__(self, job: Job, job_controller: JobController, *, task: Task, call_next: JobHandler) -> None:
        try:
            await call_next(job, job_controller)
        except Exception as err:
            for exception_type, exception_handler in self.exception_handlers.items():
                if isinstance(err, exception_type):
                    await exception_handler(err, job, job_controller)
                    return
            raise err

        await job_controller.set_success_status(job.task_result)
