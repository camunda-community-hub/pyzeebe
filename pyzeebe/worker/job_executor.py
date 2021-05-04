import asyncio
import logging

from pyzeebe.errors import JobAlreadyDeactivatedError
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task

logger = logging.getLogger(__name__)


class JobExecutor:
    def __init__(self, task: Task, jobs: asyncio.Queue):
        self.task = task
        self.jobs = jobs
        self.stop_event = asyncio.Event()

    async def execute(self) -> None:
        while self.should_execute():
            job = await self.get_next_job()
            task = asyncio.create_task(
                self.execute_one_job(job), name=f"{self.task.type}-{job.key}"
            )
            task.add_done_callback(lambda future: self.jobs.task_done())

    async def get_next_job(self) -> Job:
        return await self.jobs.get()

    async def execute_one_job(self, job: Job) -> None:
        try:
            return await self.task.job_handler(job)
        except JobAlreadyDeactivatedError as error:
            logger.warn(
                f"Job was already deactivated. Job key: {error.job_key}"
            )

    def should_execute(self) -> bool:
        return not self.stop_event.is_set()

    async def stop(self) -> None:
        self.stop_event.set()
        await self.jobs.join()
