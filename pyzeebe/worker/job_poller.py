import asyncio
import logging

from pyzeebe.errors import (ActivateJobsRequestInvalidError,
                            ZeebeBackPressureError,
                            ZeebeGatewayUnavailableError, ZeebeInternalError)
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.task.task import Task

logger = logging.getLogger(__name__)


class JobPoller:
    def __init__(self, zeebe_adapter: ZeebeAdapter, task: Task, queue: asyncio.Queue, worker_name: str, request_timeout: int):
        self.zeebe_adapter = zeebe_adapter
        self.task = task
        self.queue = queue
        self.worker_name = worker_name
        self.request_timeout = request_timeout
        self.stop_event = asyncio.Event()

    async def poll(self):
        while self.should_poll():
            await self.poll_once()

    async def poll_once(self):
        try:
            jobs = self.zeebe_adapter.activate_jobs(
                self.task.type,
                self.worker_name,
                self.task.config.timeout_ms,
                self.task.config.max_jobs_to_activate,
                self.task.config.variables_to_fetch,
                self.request_timeout,
            )
            async for job in jobs:
                await self.queue.put(job)
        except ActivateJobsRequestInvalidError:
            logger.warn(
                f"Activate job requests was invalid for task {self.task.type}"
            )
            raise
        except (ZeebeBackPressureError, ZeebeGatewayUnavailableError, ZeebeInternalError) as error:
            logger.warn(
                f"Failed to activate jobs from the gateway. Exception: {str(error)}. Retrying in 5 seconds..."
            )
            await asyncio.sleep(5)

    def should_poll(self) -> bool:
        return not self.stop_event.is_set() and (self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection)

    async def stop(self):
        self.stop_event.set()
        await self.queue.join()
