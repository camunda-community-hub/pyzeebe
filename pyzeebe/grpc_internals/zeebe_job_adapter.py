import json
import logging
from typing import Dict, List, Generator

import grpc
from zeebe_grpc.gateway_pb2 import ActivateJobsRequest, CompleteJobRequest, CompleteJobResponse, FailJobRequest, \
    FailJobResponse, ThrowErrorRequest, ThrowErrorResponse

from pyzeebe.exceptions import ActivateJobsRequestInvalid, JobAlreadyDeactivated, JobNotFound
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.job.job import Job

logger = logging.getLogger(__name__)


class ZeebeJobAdapter(ZeebeAdapterBase):
    def activate_jobs(self, task_type: str, worker: str, timeout: int, max_jobs_to_activate: int,
                      variables_to_fetch: List[str], request_timeout: int) -> Generator[Job, None, None]:
        try:
            for response in self._gateway_stub.ActivateJobs(
                    ActivateJobsRequest(type=task_type, worker=worker, timeout=timeout,
                                        maxJobsToActivate=max_jobs_to_activate,
                                        fetchVariable=variables_to_fetch, requestTimeout=request_timeout)):
                for raw_job in response.jobs:
                    job = self._create_job_from_raw_job(raw_job)
                    logger.debug(f"Got job: {job} from zeebe")
                    yield job
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ActivateJobsRequestInvalid(task_type, worker, timeout, max_jobs_to_activate)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def _create_job_from_raw_job(self, response) -> Job:
        return Job(key=response.key, _type=response.type,
                   workflow_instance_key=response.workflowInstanceKey,
                   bpmn_process_id=response.bpmnProcessId,
                   workflow_definition_version=response.workflowDefinitionVersion,
                   workflow_key=response.workflowKey,
                   element_id=response.elementId,
                   element_instance_key=response.elementInstanceKey,
                   custom_headers=json.loads(response.customHeaders),
                   worker=response.worker,
                   retries=response.retries,
                   deadline=response.deadline,
                   variables=json.loads(response.variables),
                   zeebe_adapter=self)

    def complete_job(self, job_key: int, variables: Dict) -> CompleteJobResponse:
        try:
            return self._gateway_stub.CompleteJob(CompleteJobRequest(jobKey=job_key, variables=json.dumps(variables)))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFound(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivated(job_key=job_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def fail_job(self, job_key: int, message: str) -> FailJobResponse:
        try:
            return self._gateway_stub.FailJob(FailJobRequest(jobKey=job_key, errorMessage=message))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFound(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivated(job_key=job_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def throw_error(self, job_key: int, message: str) -> ThrowErrorResponse:
        try:
            return self._gateway_stub.ThrowError(
                ThrowErrorRequest(jobKey=job_key, errorMessage=message))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFound(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivated(job_key=job_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)
