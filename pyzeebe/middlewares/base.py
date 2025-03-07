from __future__ import annotations

import logging
from collections.abc import Mapping

from pyzeebe.job.job import Job, JobController
from pyzeebe.task.exception_handler import ExceptionHandler

from .types import ConsumeMiddlewareStack, ExecuteMiddlewareStack

logger = logging.getLogger(__name__)


class BaseMiddleware:
    async def consume_scope(self, call_next: ConsumeMiddlewareStack, job: Job) -> Job:
        return await call_next(job)

    async def execute_scope(self, call_next: ExecuteMiddlewareStack, job: Job, job_controller: JobController) -> Job:
        return await call_next(job, job_controller)


class ExceptionMiddleware(BaseMiddleware):
    def __init__(self, exception_handlers: Mapping[type[Exception], ExceptionHandler]) -> None:
        assert Exception in exception_handlers

        self.exception_handlers = exception_handlers

    async def execute_scope(self, call_next: ExecuteMiddlewareStack, job: Job, job_controller: JobController) -> Job:
        try:
            job = await call_next(job, job_controller)
        except Exception as err:
            handler = self.exception_handlers.get(type(err), self.exception_handlers[Exception])
            await handler(err, job, job_controller)
        else:
            await job_controller.set_success_status(job.task_result)

        return job
