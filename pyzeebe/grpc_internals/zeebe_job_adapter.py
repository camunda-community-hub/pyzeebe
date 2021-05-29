import json
import logging
from typing import AsyncGenerator, Dict, List

import grpc
from zeebe_grpc.gateway_pb2 import (ActivateJobsRequest, CompleteJobRequest,
                                    CompleteJobResponse, FailJobRequest,
                                    FailJobResponse, ThrowErrorRequest,
                                    ThrowErrorResponse)

from pyzeebe.errors import (ActivateJobsRequestInvalidError,
                            JobAlreadyDeactivatedError, JobNotFoundError)
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.job.job import Job

logger = logging.getLogger(__name__)


class ZeebeJobAdapter(ZeebeAdapterBase):
    async def activate_jobs(self, task_type: str, worker: str, timeout: int, max_jobs_to_activate: int,
                            variables_to_fetch: List[str], request_timeout: int) -> AsyncGenerator[Job, None]:
        try:
            async for response in self._gateway_stub.ActivateJobs(
                    ActivateJobsRequest(type=task_type, worker=worker, timeout=timeout,
                                        maxJobsToActivate=max_jobs_to_activate,
                                        fetchVariable=variables_to_fetch, requestTimeout=request_timeout)):
                for raw_job in response.jobs:
                    job = self._create_job_from_raw_job(raw_job)
                    logger.debug(f"Got job: {job} from zeebe")
                    yield job
        except grpc.aio.AioRpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ActivateJobsRequestInvalidError(
                    task_type, worker, timeout, max_jobs_to_activate)
            else:
                await self._common_zeebe_grpc_errors(rpc_error)

    def _create_job_from_raw_job(self, response) -> Job:
        return Job(key=response.key, _type=response.type,
                   process_instance_key=response.processInstanceKey,
                   bpmn_process_id=response.bpmnProcessId,
                   process_definition_version=response.processDefinitionVersion,
                   process_definition_key=response.processDefinitionKey,
                   element_id=response.elementId,
                   element_instance_key=response.elementInstanceKey,
                   custom_headers=json.loads(response.customHeaders),
                   worker=response.worker,
                   retries=response.retries,
                   deadline=response.deadline,
                   variables=json.loads(response.variables),
                   zeebe_adapter=self)

    async def complete_job(self, job_key: int, variables: Dict) -> CompleteJobResponse:
        try:
            return await self._gateway_stub.CompleteJob(CompleteJobRequest(jobKey=job_key, variables=json.dumps(variables)))
        except grpc.aio.AioRpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key)
            else:
                await self._common_zeebe_grpc_errors(rpc_error)

    async def fail_job(self, job_key: int, retries: int, message: str) -> FailJobResponse:
        try:
            return await self._gateway_stub.FailJob(FailJobRequest(jobKey=job_key, retries=retries, errorMessage=message))
        except grpc.aio.AioRpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key)
            else:
                await self._common_zeebe_grpc_errors(rpc_error)

    async def throw_error(self, job_key: int, message: str, error_code: str = "") -> ThrowErrorResponse:
        try:
            return await self._gateway_stub.ThrowError(
                ThrowErrorRequest(jobKey=job_key, errorMessage=message, errorCode=error_code))
        except grpc.aio.AioRpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key)
            else:
                await self._common_zeebe_grpc_errors(rpc_error)
