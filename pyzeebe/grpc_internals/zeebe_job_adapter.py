from __future__ import annotations

import json
import logging
import types
from collections.abc import AsyncGenerator, Iterable

import grpc
from zeebe_grpc.gateway_pb2 import (
    ActivatedJob,
    ActivateJobsRequest,
    CompleteJobRequest,
    FailJobRequest,
    ThrowErrorRequest,
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

from .types import CompleteJobResponse, FailJobResponse, ThrowErrorResponse

logger = logging.getLogger(__name__)

DEFAULT_GRPC_REQUEST_TIMEOUT = 20  # This constant represents the fallback timeout value


class ZeebeJobAdapter(ZeebeAdapterBase):
    async def activate_jobs(
        self,
        task_type: str,
        worker: str,
        timeout: int,
        max_jobs_to_activate: int,
        variables_to_fetch: Iterable[str],
        request_timeout: int,
        tenant_ids: Iterable[str] | None = None,
    ) -> AsyncGenerator[Job]:
        try:
            grpc_request_timeout = request_timeout / 1000 * 2 if request_timeout > 0 else DEFAULT_GRPC_REQUEST_TIMEOUT
            async for response in self._gateway_stub.ActivateJobs(
                ActivateJobsRequest(
                    type=task_type,
                    worker=worker,
                    timeout=timeout,
                    maxJobsToActivate=max_jobs_to_activate,
                    fetchVariable=variables_to_fetch,
                    requestTimeout=request_timeout,
                    tenantIds=tenant_ids,
                ),
                timeout=grpc_request_timeout,
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
            custom_headers=types.MappingProxyType(json.loads(response.customHeaders)),
            worker=response.worker,
            retries=response.retries,
            deadline=response.deadline,
            variables=types.MappingProxyType(json.loads(response.variables)),
            tenant_id=response.tenantId,
        )

    async def complete_job(self, job_key: int, variables: Variables) -> CompleteJobResponse:
        try:
            await self._gateway_stub.CompleteJob(CompleteJobRequest(jobKey=job_key, variables=json.dumps(variables)))
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key) from grpc_error
            elif is_error_status(grpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

        return CompleteJobResponse()

    async def fail_job(
        self, job_key: int, retries: int, message: str, retry_back_off_ms: int, variables: Variables
    ) -> FailJobResponse:
        try:
            await self._gateway_stub.FailJob(
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

        return FailJobResponse()

    async def throw_error(
        self, job_key: int, message: str, variables: Variables, error_code: str = ""
    ) -> ThrowErrorResponse:
        try:
            await self._gateway_stub.ThrowError(
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

        return ThrowErrorResponse()
