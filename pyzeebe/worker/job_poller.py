import asyncio
import logging

from pyzeebe.errors import (ActivateJobsRequestInvalidError,
                            ZeebeBackPressureError,
                            ZeebeGatewayUnavailableError, ZeebeInternalError)
from pyzeebe.grpc_internals.zeebe_job_adapter import ZeebeJobAdapter
from pyzeebe.task.task import Task
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)


class JobPoller:
    def __init__(self, zeebe_adapter: ZeebeJobAdapter, task: Task, queue: asyncio.Queue, worker_name: str,
                 request_timeout: int, task_state: TaskState, poll_retry_delay: int):
        self.zeebe_adapter = zeebe_adapter
        self.task = task
        self.queue = queue
        self.worker_name = worker_name
        self.request_timeout = request_timeout
        self.task_state = task_state
        self.poll_retry_delay = poll_retry_delay
        self.stop_event = asyncio.Event()

    async def poll(self):
        while self.should_poll():
            await self.activate_max_jobs()

    async def activate_max_jobs(self):
        if self.calculate_max_jobs_to_activate() > 0:
            await self.poll_once()
        else:
            logger.warning(f"Maximum number of jobs running for {self.task.type}. Polling again in {self.poll_retry_delay} seconds...")
            await asyncio.sleep(self.poll_retry_delay)

    async def poll_once(self):
        try:
            jobs = self.zeebe_adapter.activate_jobs(
                task_type=self.task.type,
                worker=self.worker_name,
                timeout=self.task.config.timeout_ms,
                max_jobs_to_activate=self.calculate_max_jobs_to_activate(),
                variables_to_fetch=self.task.config.variables_to_fetch,
                request_timeout=self.request_timeout,
            )
            async for job in jobs:
                self.task_state.add(job)
                await self.queue.put(job)
        except ActivateJobsRequestInvalidError:
            logger.warning(
                f"Activate job requests was invalid for task {self.task.type}"
            )
            raise
        except (ZeebeBackPressureError, ZeebeGatewayUnavailableError, ZeebeInternalError) as error:
            logger.warning(
                f"Failed to activate jobs from the gateway. Exception: {repr(error)}. Retrying in 5 seconds..."
            )
            await asyncio.sleep(5)

    def should_poll(self) -> bool:
        return not self.stop_event.is_set() \
            and (self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection)

    def calculate_max_jobs_to_activate(self) -> int:
        worker_max_jobs = self.task.config.max_running_jobs - self.task_state.count_active()
        return min(worker_max_jobs, self.task.config.max_jobs_to_activate)

    async def stop(self):
        self.stop_event.set()
        await self.queue.join()
