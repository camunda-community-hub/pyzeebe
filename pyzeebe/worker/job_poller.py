from __future__ import annotations

import asyncio
import logging

from pyzeebe.errors import (
    ActivateJobsRequestInvalidError,
    StreamActivateJobsRequestInvalidError,
    ZeebeBackPressureError,
    ZeebeDeadlineExceeded,
    ZeebeGatewayUnavailableError,
    ZeebeInternalError,
)
from pyzeebe.grpc_internals.zeebe_job_adapter import ZeebeJobAdapter
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)


class JobPoller:
    def __init__(
        self,
        zeebe_adapter: ZeebeJobAdapter,
        task: Task,
        queue: asyncio.Queue[Job],
        worker_name: str,
        request_timeout: int,
        task_state: TaskState,
        poll_retry_delay: int,
        tenant_ids: list[str] | None,
    ) -> None:
        self.zeebe_adapter = zeebe_adapter
        self.task = task
        self.queue = queue
        self.worker_name = worker_name
        self.request_timeout = request_timeout
        self.task_state = task_state
        self.poll_retry_delay = poll_retry_delay
        self.tenant_ids = tenant_ids
        self.stop_event = asyncio.Event()

    async def poll(self) -> None:
        while self.should_poll():
            await self.activate_max_jobs()

    async def activate_max_jobs(self) -> None:
        if self.calculate_max_jobs_to_activate() > 0:
            await self.poll_once()
        else:
            logger.warning(
                "Maximum number of jobs running for %s. Polling again in %s seconds...",
                self.task.type,
                self.poll_retry_delay,
            )
            await asyncio.sleep(self.poll_retry_delay)

    async def poll_once(self) -> None:
        try:
            jobs = self.zeebe_adapter.activate_jobs(
                task_type=self.task.type,
                worker=self.worker_name,
                timeout=self.task.config.timeout_ms,
                max_jobs_to_activate=self.calculate_max_jobs_to_activate(),
                variables_to_fetch=self.task.config.variables_to_fetch or [],
                request_timeout=self.request_timeout,
                tenant_ids=self.tenant_ids,
            )
            async for job in jobs:
                self.task_state.add(job)
                await self.queue.put(job)
        except ActivateJobsRequestInvalidError:
            logger.warning("Activate job requests was invalid for task %s", self.task.type)
            raise
        except (
            ZeebeBackPressureError,
            ZeebeGatewayUnavailableError,
            ZeebeInternalError,
            ZeebeDeadlineExceeded,
        ) as error:
            logger.warning(
                "Failed to activate jobs from the gateway. Exception: %s. Retrying in 5 seconds...",
                repr(error),
            )
            await asyncio.sleep(5)

    def should_poll(self) -> bool:
        return not self.stop_event.is_set() and (self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection)

    def calculate_max_jobs_to_activate(self) -> int:
        worker_max_jobs = self.task.config.max_running_jobs - self.task_state.count_active()
        return min(worker_max_jobs, self.task.config.max_jobs_to_activate)

    async def stop(self) -> None:
        self.stop_event.set()
        await self.queue.join()


class JobStreamer:
    def __init__(
        self,
        zeebe_adapter: ZeebeJobAdapter,
        task: Task,
        queue: asyncio.Queue[Job],
        worker_name: str,
        stream_request_timeout: int,
        task_state: TaskState,
        tenant_ids: list[str] | None,
    ) -> None:
        self.zeebe_adapter = zeebe_adapter
        self.task = task
        self.queue = queue
        self.worker_name = worker_name
        self.stream_request_timeout = stream_request_timeout
        self.task_state = task_state
        self.tenant_ids = tenant_ids
        self.stop_event = asyncio.Event()

    async def poll(self) -> None:
        while self.should_poll():
            await self.activate_stream()

    async def activate_stream(self) -> None:
        try:
            jobs = self.zeebe_adapter.stream_activate_jobs(
                task_type=self.task.type,
                worker=self.worker_name,
                timeout=self.task.config.timeout_ms,
                variables_to_fetch=self.task.config.variables_to_fetch or [],
                stream_request_timeout=self.stream_request_timeout,
                tenant_ids=self.tenant_ids,
            )
            async for job in jobs:
                self.task_state.add(job)
                await self.queue.put(job)
        except StreamActivateJobsRequestInvalidError:
            logger.warning("Stream job requests was invalid for task %s", self.task.type)
            raise
        except (
            ZeebeBackPressureError,
            ZeebeGatewayUnavailableError,
            ZeebeInternalError,
            ZeebeDeadlineExceeded,
        ) as error:
            logger.warning(
                "Failed to strean jobs from the gateway. Exception: %s. Retrying in 5 seconds...",
                repr(error),
            )
            await asyncio.sleep(5)

    def should_poll(self) -> bool:
        return not self.stop_event.is_set() and (self.zeebe_adapter.connected or self.zeebe_adapter.retrying_connection)

    async def stop(self) -> None:
        self.stop_event.set()
        await self.queue.join()
