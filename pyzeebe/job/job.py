import copy
from typing import Dict

from pyzeebe.errors import NoZeebeAdapterError
from pyzeebe.job.job_status import JobStatus


class Job(object):
    def __init__(self, key: int, _type: str, process_instance_key: int, bpmn_process_id: str,
                 process_definition_version: int, process_definition_key: int, element_id: str, element_instance_key: int,
                 custom_headers: Dict, worker: str, retries: int, deadline: int, variables: Dict,
                 status: JobStatus = JobStatus.Running, zeebe_adapter=None):
        self.key = key
        self.type = _type
        self.process_instance_key = process_instance_key
        self.bpmn_process_id = bpmn_process_id
        self.process_definition_version = process_definition_version
        self.process_definition_key = process_definition_key
        self.element_id = element_id
        self.element_instance_key = element_instance_key
        self.custom_headers = custom_headers
        self.worker = worker
        self.retries = retries
        self.deadline = deadline
        self.variables = variables
        self.status = status
        self.zeebe_adapter = zeebe_adapter

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
            await self.zeebe_adapter.complete_job(job_key=self.key, variables=self.variables)
        else:
            raise NoZeebeAdapterError()

    async def set_failure_status(self, message: str) -> None:
        """
        Failure status means a technical error has occurred. If retried the job may succeed.
        For example: connection to DB lost

        Args:
            message (str): The failure message that Zeebe will receive

        Raises:
            NoZeebeAdapterError: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            await self.zeebe_adapter.fail_job(job_key=self.key, retries=self.retries-1, message=message)
        else:
            raise NoZeebeAdapterError()

    async def set_error_status(self, message: str, error_code: str = "") -> None:
        """
        Error status means that the job could not be completed because of a business error and won't ever be able to be completed.
        For example: a required parameter was not given
        An error code can be added to handle the error in the Zeebe process

        Args:
            message (str): The error message
            error_code (str): The error code that Zeebe will receive

        Raises:
            NoZeebeAdapterError: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            await self.zeebe_adapter.throw_error(job_key=self.key, message=message, error_code=error_code)
        else:
            raise NoZeebeAdapterError()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            raise NotImplementedError()
        return self.key == other.key

    def __repr__(self):
        return str({"jobKey": self.key, "taskType": self.type, "processInstanceKey": self.process_instance_key,
                    "bpmnProcessId": self.bpmn_process_id,
                    "processDefinitionVersion": self.process_definition_version, "processDefinitionKey": self.process_definition_key,
                    "elementId": self.element_id, "elementInstanceKey": self.element_instance_key,
                    "customHeaders": self.custom_headers, "worker": self.worker, "retries": self.retries,
                    "deadline": self.deadline, "variables": self.variables})

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
        job.status,
        job.zeebe_adapter
    )
