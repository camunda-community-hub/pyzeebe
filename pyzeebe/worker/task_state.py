import logging
from pyzeebe import Job

logger = logging.getLogger(__name__)

class TaskState:
    def __init__(self):
        self._data = set()

    def remove(self, job: Job) -> None:
        try:
            self._data.remove(job.key)
        except KeyError:
            logger.warning(f"Could not find Job key {job.key} when trying to remove from TaskState")

    def add(self, job: Job) -> None:
        if job.key in self._data:
            raise ValueError(f"Job {job.key} already registered in TaskState")
        self._data.add(job.key)

    def count_active(self) -> int:
        return len(self._data)
