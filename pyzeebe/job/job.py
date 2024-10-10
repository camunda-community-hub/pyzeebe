from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyzeebe.job.job_status import JobStatus
from pyzeebe.types import Headers, Variables

if TYPE_CHECKING:
    from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter


@dataclass(frozen=True)
class Job:
    key: int
    type: str
    process_instance_key: int
    bpmn_process_id: str
    process_definition_version: int
    process_definition_key: int
    element_id: str
    element_instance_key: int
    custom_headers: Headers
    worker: str
    retries: int
    deadline: int
    variables: Variables
    tenant_id: str | None = None
    status: JobStatus = JobStatus.Running
    task_result = None

    def set_task_result(self, task_result: Any) -> None:
        object.__setattr__(self, "task_result", task_result)

    def _set_status(self, value: JobStatus) -> None:
        object.__setattr__(self, "status", value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return self.key == other.key


class JobController:
    def __init__(self, job: Job, zeebe_adapter: ZeebeAdapter) -> None:
        self._job = job
        self._zeebe_adapter = zeebe_adapter

    async def set_running_after_decorators_status(self) -> None:
        """
        RunningAfterDecorators status means that the task has been completed as intended and the after decorators will now run.
        """
        self._job._set_status(JobStatus.RunningAfterDecorators)

    async def set_success_status(self, variables: Variables | None = None) -> None:
        """
        Success status means that the job has been completed as intended.

        Raises:
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        self._job._set_status(JobStatus.Completed)
        await self._zeebe_adapter.complete_job(job_key=self._job.key, variables=variables or {})

    async def set_failure_status(
        self,
        message: str,
        retry_back_off_ms: int = 0,
        variables: Variables | None = None,
    ) -> None:
        """
        Failure status means a technical error has occurred. If retried the job may succeed.
        For example: connection to DB lost

        Args:
            message (str): The failure message that Zeebe will receive
            retry_back_off_ms (int): The backoff timeout (in ms) for the next retry. New in Zeebe 8.1.
            variables (dict): A dictionary containing variables that will instantiate the variables at
                the local scope of the job's associated task. Must be JSONable. New in Zeebe 8.2.

        Raises:
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        self._job._set_status(JobStatus.Failed)
        await self._zeebe_adapter.fail_job(
            job_key=self._job.key,
            retries=self._job.retries - 1,
            message=message,
            retry_back_off_ms=retry_back_off_ms,
            variables=variables or {},
        )

    async def set_error_status(
        self,
        message: str,
        error_code: str = "",
        variables: Variables | None = None,
    ) -> None:
        """
        Error status means that the job could not be completed because of a business error and won't ever be able to be completed.
        For example: a required parameter was not given
        An error code can be added to handle the error in the Zeebe process

        Args:
            message (str): The error message
            error_code (str): The error code that Zeebe will receive
            variables (dict): A dictionary containing variables that will instantiate the variables at
                the local scope of the job's associated task. Must be JSONable. New in Zeebe 8.2.

        Raises:
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        self._job._set_status(JobStatus.ErrorThrown)
        await self._zeebe_adapter.throw_error(
            job_key=self._job.key, message=message, error_code=error_code, variables=variables or {}
        )
