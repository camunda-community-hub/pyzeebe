import asyncio
import datetime
import logging

from pyzeebe.errors import (
    ActivateJobsRequestInvalidError,
    ZeebeBackPressureError,
    ZeebeGatewayUnavailableError,
    ZeebeInternalError,
)
from pyzeebe.grpc_internals.zeebe_job_adapter import ZeebeJobAdapter
from pyzeebe.task.task import Task
from pyzeebe.worker.task_state import TaskState

logger = logging.getLogger(__name__)


class JobPoller:
    last_poll_time: datetime.datetime = datetime.datetime.now()

    def __init__(
        self,
        zeebe_adapter: ZeebeJobAdapter,
        task: Task,
        queue: asyncio.Queue,
        worker_name: str,
        request_timeout: int,
        task_state: TaskState,
        poll_retry_delay: int,
    ):
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
            logger.info(f"pool self = {str(self)}")
            await self.activate_max_jobs()

    async def activate_max_jobs(self):
        if self.calculate_max_jobs_to_activate() > 0:
            await self.poll_once()
        else:
            logger.warning(
                "Maximum number of jobs running for %s. Polling again in %s seconds...",
                self.task.type,
                self.poll_retry_delay,
            )
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
            logger.warning("Activate job requests was invalid for task %s", self.task.type)
            raise
        except (ZeebeBackPressureError, ZeebeGatewayUnavailableError, ZeebeInternalError) as error:
            logger.warning(
                "Failed to activate jobs from the gateway. Exception: %s. Retrying in 5 seconds...",
                repr(error),
            )
            await asyncio.sleep(5)

    def should_poll(self) -> bool:
        stop_event = self.stop_event.is_set()
        zeebe_adapter_connected = self.zeebe_adapter.connected
        zeebe_adapter_retrying_connection = self.zeebe_adapter.retrying_connection
        logger.info(
            f"should_poll stop_event = {stop_event} , zeebe_adapter_connected = {zeebe_adapter_connected} , zeebe_adapter_retrying_connection = {zeebe_adapter_retrying_connection}"
        )
        JobPoller.last_poll_time = datetime.datetime.now()
        return not stop_event and (zeebe_adapter_connected or zeebe_adapter_retrying_connection)

    def calculate_max_jobs_to_activate(self) -> int:
        worker_max_jobs = self.task.config.max_running_jobs - self.task_state.count_active()
        return min(worker_max_jobs, self.task.config.max_jobs_to_activate)

    async def stop(self):
        logger.info(f"JobPoller stop event {self}")
        self.stop_event.set()
        await self.queue.join()

    def __repr__(self):
        return "<JobPoller(zeebe_adapter='{}', task='{}', queue='{}'" \
               ", worker_name='{}', request_timeout='{}', task_state='{}', poll_retry_delay='{}'" \
               ", stop_event='{}')>" \
            .format(self.zeebe_adapter, self.task, self.queue, self.worker_name, self.request_timeout, self.task_state,
                    self.poll_retry_delay, self.stop_event)
