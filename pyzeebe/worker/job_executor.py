from __future__ import annotations

import asyncio
import logging
from functools import partial
from typing import Callable

from pyzeebe.errors import JobAlreadyDeactivatedError
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job, JobController
from pyzeebe.middlewares import BaseMiddleware, ExecuteMiddlewareStack
from pyzeebe.task.task import Task
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)

AsyncTaskCallback = Callable[["asyncio.Future[None]"], None]


class JobExecutor:
    def __init__(
        self,
        *,
        task: Task,
        jobs: asyncio.Queue[Job],
        task_state: TaskState,
        zeebe_adapter: ZeebeAdapter,
        middlewares: list[BaseMiddleware],
    ):
        self.task = task
        self.jobs = jobs
        self.task_state = task_state
        self.stop_event = asyncio.Event()
        self.zeebe_adapter = zeebe_adapter
        self.middleware_stack = self._build_middleware_execute_stack(middlewares)

    async def execute(self) -> None:
        while self.should_execute():
            job = await self.get_next_job()
            task = asyncio.create_task(self.execute_one_job(JobController(job, self.zeebe_adapter)))
            task.add_done_callback(create_job_callback(self, job))

    async def get_next_job(self) -> Job:
        return await self.jobs.get()

    async def execute_one_job(self, job_controller: JobController) -> None:
        try:
            await self.middleware_stack(job_controller.job, job_controller)
        except JobAlreadyDeactivatedError as error:
            logger.warning("Job was already deactivated. Job key: %s", error.job_key)

    def should_execute(self) -> bool:
        return not self.stop_event.is_set()

    async def stop(self) -> None:
        self.stop_event.set()
        await self.jobs.join()

    def _build_middleware_execute_stack(self, middlewares: list[BaseMiddleware]) -> ExecuteMiddlewareStack:
        job_handler = self.task.job_handler

        for m in middlewares:
            job_handler = partial(m.execute_scope, job_handler)

        return job_handler


def create_job_callback(job_executor: JobExecutor, job: Job) -> AsyncTaskCallback:
    def callback(fut: asyncio.Future[None]) -> None:
        err = fut.done() and not fut.cancelled() and fut.exception()
        if err:
            logger.exception("Error in job executor. Task: %s. Error: %s.", job.type, err, exc_info=err)

        job_executor.jobs.task_done()
        job_executor.task_state.remove(job)

    return callback
