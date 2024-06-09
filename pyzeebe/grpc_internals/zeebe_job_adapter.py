import json
import logging
from typing import AsyncGenerator, Iterable, Optional

import grpc
from zeebe_grpc.gateway_pb2 import (
    ActivatedJob,
    ActivateJobsRequest,
    CompleteJobRequest,
    CompleteJobResponse,
    FailJobRequest,
    FailJobResponse,
    ThrowErrorRequest,
    ThrowErrorResponse,
)

from pyzeebe.errors import (
    ActivateJobsRequestInvalidError,
    JobAlreadyDeactivatedError,
    JobNotFoundError,
)
from pyzeebe.grpc_internals.grpc_utils import is_error_status
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.job.job import Job
from pyzeebe.types import Variables

logger = logging.getLogger(__name__)


class ZeebeJobAdapter(ZeebeAdapterBase):
    async def activate_jobs(
        self,
        task_type: str,
        worker: str,
        timeout: int,
        max_jobs_to_activate: int,
        variables_to_fetch: Iterable[str],
        request_timeout: int,
        tenant_ids: Optional[Iterable[str]] = None,
    ) -> AsyncGenerator[Job, None]:
        try:
            async for response in self._gateway_stub.ActivateJobs(
                ActivateJobsRequest(
                    type=task_type,
                    worker=worker,
                    timeout=timeout,
                    maxJobsToActivate=max_jobs_to_activate,
                    fetchVariable=variables_to_fetch,
                    requestTimeout=request_timeout,
                    tenantIds=tenant_ids,
                )
            ):
                for raw_job in response.jobs:
                    job = self._create_job_from_raw_job(raw_job)
                    logger.debug("Got job: %s from zeebe", job)
                    yield job
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ActivateJobsRequestInvalidError(task_type, worker, timeout, max_jobs_to_activate) from grpc_error
            await self._handle_grpc_error(grpc_error)

    def _create_job_from_raw_job(self, response: ActivatedJob) -> Job:
        return Job(
            key=response.key,
            type=response.type,
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
            tenant_id=response.tenantId,
            zeebe_adapter=self,  # type: ignore[arg-type]
        )

    async def complete_job(self, job_key: int, variables: Variables) -> CompleteJobResponse:
        try:
            return await self._gateway_stub.CompleteJob(
                CompleteJobRequest(jobKey=job_key, variables=json.dumps(variables))
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key) from grpc_error
            elif is_error_status(grpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

    async def fail_job(
        self, job_key: int, retries: int, message: str, retry_back_off_ms: int, variables: Variables
    ) -> FailJobResponse:
        try:
            return await self._gateway_stub.FailJob(
                FailJobRequest(
                    jobKey=job_key,
                    retries=retries,
                    errorMessage=message,
                    retryBackOff=retry_back_off_ms,
                    variables=json.dumps(variables),
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key) from grpc_error
            elif is_error_status(grpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

    async def throw_error(
        self, job_key: int, message: str, variables: Variables, error_code: str = ""
    ) -> ThrowErrorResponse:
        try:
            return await self._gateway_stub.ThrowError(
                ThrowErrorRequest(
                    jobKey=job_key,
                    errorMessage=message,
                    errorCode=error_code,
                    variables=json.dumps(variables),
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key) from grpc_error
            elif is_error_status(grpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key) from grpc_error
            await self._handle_grpc_error(grpc_error)
