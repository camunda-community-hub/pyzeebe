from typing import Dict

from pyzeebe.exceptions import NoZeebeAdapter
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

    def set_success_status(self) -> None:
        """
        Success status means that the job has been completed as intended.

        Raises:
            NoZeebeAdapter: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressure: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailable: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            self.zeebe_adapter.complete_job(
                job_key=self.key, variables=self.variables)
        else:
            raise NoZeebeAdapter()

    def set_failure_status(self, message: str) -> None:
        """
        Failure status means a technical error has occurred. If retried the job may succeed.
        For example: connection to DB lost

        Args:
            message (str): The failure message that Zeebe will receive

        Raises:
            NoZeebeAdapter: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressure: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailable: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            self.zeebe_adapter.fail_job(job_key=self.key, message=message)
        else:
            raise NoZeebeAdapter()

    def set_error_status(self, message: str) -> None:
        """
        Error status means that the job could not be completed because of a business error and won't ever be able to be completed.
        For example: a required parameter was not given

        Args:
            message (str): The error message that Zeebe will receive

        Raises:
            NoZeebeAdapter: If the job does not have a configured ZeebeAdapter
            ZeebeBackPressure: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailable: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        if self.zeebe_adapter:
            self.zeebe_adapter.throw_error(job_key=self.key, message=message)
        else:
            raise NoZeebeAdapter()

    def __repr__(self):
        return str({"jobKey": self.key, "taskType": self.type, "processInstanceKey": self.process_instance_key,
                    "bpmnProcessId": self.bpmn_process_id,
                    "processDefinitionVersion": self.process_definition_version, "processDefinitionKey": self.process_definition_key,
                    "elementId": self.element_id, "elementInstanceKey": self.element_instance_key,
                    "customHeaders": self.custom_headers, "worker": self.worker, "retries": self.retries,
                    "deadline": self.deadline, "variables": self.variables})
