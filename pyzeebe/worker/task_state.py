import logging

from pyzeebe import Job

logger = logging.getLogger(__name__)


class TaskState:
    def __init__(self):
        self._active_jobs = set()

    def remove(self, job: Job) -> None:
        try:
            self._active_jobs.remove(job.key)
        except KeyError:
            logger.warning(
                f"Could not find Job key {job.key} when trying to remove from TaskState")

    def add(self, job: Job) -> None:
        if job.key in self._active_jobs:
            raise ValueError(f"Job {job.key} already registered in TaskState")
        self._active_jobs.add(job.key)

    def count_active(self) -> int:
        return len(self._active_jobs)
