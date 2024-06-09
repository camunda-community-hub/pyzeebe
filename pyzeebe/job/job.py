import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

from pyzeebe.errors import NoZeebeAdapterError
from pyzeebe.job.job_status import JobStatus
from pyzeebe.types import Variables

if TYPE_CHECKING:
    from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter


@dataclass
class Job:
    key: int
    type: str
    process_instance_key: int
    bpmn_process_id: str
    process_definition_version: int
    process_definition_key: int
    element_id: str
    element_instance_key: int
    custom_headers: Dict[str, Any]
    worker: str
    retries: int
    deadline: int
    variables: Variables
    tenant_id: Optional[str] = None
    status: JobStatus = JobStatus.Running
    zeebe_adapter: Optional["ZeebeAdapter"] = None

    async def set_running_after_decorators_status(self) -> None:
        """
        RunningAfterDecorators status means that the task has been completed as intended and the after decorators will now run.

        Raises:
            NoZeebeAdapterError: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            self.status = JobStatus.RunningAfterDecorators
        else:
            raise NoZeebeAdapterError()

    async def set_success_status(self) -> None:
        """
        Success status means that the job has been completed as intended.

        Raises:
            NoZeebeAdapterError: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            self.status = JobStatus.Completed
            await self.zeebe_adapter.complete_job(job_key=self.key, variables=self.variables)
        else:
            raise NoZeebeAdapterError()

    async def set_failure_status(
        self,
        message: str,
        retry_back_off_ms: int = 0,
        variables: Optional[Variables] = None,
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
            NoZeebeAdapterError: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            self.status = JobStatus.Failed
            await self.zeebe_adapter.fail_job(
                job_key=self.key,
                retries=self.retries - 1,
                message=message,
                retry_back_off_ms=retry_back_off_ms,
                variables=variables or {},
            )
        else:
            raise NoZeebeAdapterError()

    async def set_error_status(
        self,
        message: str,
        error_code: str = "",
        variables: Optional[Variables] = None,
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
            NoZeebeAdapterError: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            self.status = JobStatus.ErrorThrown
            await self.zeebe_adapter.throw_error(
                job_key=self.key, message=message, error_code=error_code, variables=variables or {}
            )
        else:
            raise NoZeebeAdapterError()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            raise NotImplementedError()
        return self.key == other.key


def create_copy(job: Job) -> Job:
    return Job(
        job.key,
        job.type,
        job.process_instance_key,
        job.bpmn_process_id,
        job.process_definition_version,
        job.process_definition_key,
        job.element_id,
        job.element_instance_key,
        copy.deepcopy(job.custom_headers),
        job.worker,
        job.retries,
        job.deadline,
        copy.deepcopy(job.variables),
        job.tenant_id,
        job.status,
        job.zeebe_adapter,
    )
