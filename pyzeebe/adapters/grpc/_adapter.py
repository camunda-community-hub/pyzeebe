import json
import logging
import os
import types
from collections.abc import AsyncGenerator, Iterable
from typing import TYPE_CHECKING, NoReturn, cast, final

import anyio
import grpc.aio
from grpc_health.v1.health_pb2 import HealthCheckRequest
from grpc_health.v1.health_pb2_grpc import HealthStub

from pyzeebe.adapters.abc import ZeebeAdapter
from pyzeebe.adapters.types import (
    BroadcastSignalResponse,
    CancelProcessInstanceResponse,
    CompleteJobResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    DeployResourceResponse,
    EvaluateDecisionResponse,
    FailJobResponse,
    HealthCheckResponse,
    PublishMessageResponse,
    ThrowErrorResponse,
    TopologyResponse,
    UpdateJobTimeoutResponse,
)
from pyzeebe.errors import (
    ActivateJobsRequestInvalidError,
    DecisionNotFoundError,
    InvalidJSONError,
    JobAlreadyDeactivatedError,
    JobNotFoundError,
    ProcessDefinitionHasNoStartEventError,
    ProcessDefinitionNotFoundError,
    ProcessInstanceNotFoundError,
    ProcessInvalidError,
    ProcessTimeoutError,
    PyZeebeError,
    StreamActivateJobsRequestInvalidError,
    UnknownGrpcStatusCodeError,
    ZeebeBackPressureError,
    ZeebeDeadlineExceeded,
    ZeebeGatewayUnavailableError,
    ZeebeInternalError,
)
from pyzeebe.errors.message_errors import MessageAlreadyExistsError
from pyzeebe.job.job import Job
from pyzeebe.proto.gateway_pb2 import (
    ActivatedJob,
    ActivateJobsRequest,
    BroadcastSignalRequest,
    CancelProcessInstanceRequest,
    CompleteJobRequest,
    CreateProcessInstanceRequest,
    CreateProcessInstanceWithResultRequest,
    DeployResourceRequest,
    EvaluatedDecision,
    EvaluatedDecisionInput,
    EvaluatedDecisionOutput,
    EvaluateDecisionRequest,
    FailJobRequest,
    MatchedDecisionRule,
    PublishMessageRequest,
    Resource,
    StreamActivatedJobsRequest,
    ThrowErrorRequest,
    TopologyRequest,
    UpdateJobTimeoutRequest,
)
from pyzeebe.proto.gateway_pb2_grpc import GatewayStub
from pyzeebe.types import Variables

from ._metadata_parser import parse_resource_metadata
from ._utils import is_error_status

if TYPE_CHECKING:
    from pyzeebe.proto.gateway_pb2_grpc import GatewayAsyncStub

logger = logging.getLogger(__name__)

DEFAULT_GRPC_REQUEST_TIMEOUT = 20  # This constant represents the fallback timeout value


@final
class ZeebeGRPCAdapter(ZeebeAdapter):
    def __init__(self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = 10):
        """
        Args:
            grpc_channel (grpc.aio.Channel): GRPC Channel connected to a Zeebe gateway
            max_connection_retries (int): Amount of connection retries before worker gives up on connecting to zeebe. To setup with infinite retries use -1
        """
        self._channel = grpc_channel
        self._gateway_stub = cast("GatewayAsyncStub", GatewayStub(grpc_channel))
        self._health_stub = HealthStub(grpc_channel)
        self._connected = True
        self._retrying_connection = False
        self._max_connection_retries = max_connection_retries
        self._current_connection_retries = 0

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def retrying_connection(self) -> bool:
        return self._retrying_connection

    async def create_process_instance(
        self,
        bpmn_process_id: str,
        version: int,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceResponse:
        try:
            response = await self._gateway_stub.CreateProcessInstance(
                CreateProcessInstanceRequest(
                    bpmnProcessId=bpmn_process_id,
                    version=version,
                    variables=json.dumps(variables),
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            await self._create_process_errors(grpc_error, bpmn_process_id, version, variables)

        return CreateProcessInstanceResponse(
            process_definition_key=response.processDefinitionKey,
            bpmn_process_id=response.bpmnProcessId,
            version=response.version,
            process_instance_key=response.processInstanceKey,
            tenant_id=response.tenantId,
        )

    async def create_process_instance_with_result(
        self,
        bpmn_process_id: str,
        version: int,
        variables: Variables,
        timeout: int,  # noqa: ASYNC109
        variables_to_fetch: Iterable[str],
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceWithResultResponse:
        try:
            response = await self._gateway_stub.CreateProcessInstanceWithResult(
                CreateProcessInstanceWithResultRequest(
                    request=CreateProcessInstanceRequest(
                        bpmnProcessId=bpmn_process_id,
                        version=version,
                        variables=json.dumps(variables),
                        tenantId=tenant_id,  # type: ignore[arg-type]
                    ),
                    requestTimeout=timeout,
                    fetchVariables=variables_to_fetch,
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            await self._create_process_errors(grpc_error, bpmn_process_id, version, variables)

        return CreateProcessInstanceWithResultResponse(
            process_definition_key=response.processDefinitionKey,
            bpmn_process_id=response.bpmnProcessId,
            version=response.version,
            process_instance_key=response.processInstanceKey,
            variables=json.loads(response.variables),
            tenant_id=response.tenantId,
        )

    async def _create_process_errors(
        self, grpc_error: grpc.aio.AioRpcError, bpmn_process_id: str, version: int, variables: Variables
    ) -> NoReturn:
        if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
            raise ProcessDefinitionNotFoundError(bpmn_process_id=bpmn_process_id, version=version) from grpc_error
        elif is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT):
            raise InvalidJSONError(
                f"Cannot start process: {bpmn_process_id} with version {version}. Variables: {variables}"
            ) from grpc_error
        elif is_error_status(grpc_error, grpc.StatusCode.FAILED_PRECONDITION):
            raise ProcessDefinitionHasNoStartEventError(bpmn_process_id=bpmn_process_id) from grpc_error
        elif is_error_status(grpc_error, grpc.StatusCode.DEADLINE_EXCEEDED):
            raise ProcessTimeoutError(bpmn_process_id) from grpc_error
        await self._handle_grpc_error(grpc_error)

    async def cancel_process_instance(self, process_instance_key: int) -> CancelProcessInstanceResponse:
        try:
            await self._gateway_stub.CancelProcessInstance(
                CancelProcessInstanceRequest(processInstanceKey=process_instance_key)
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise ProcessInstanceNotFoundError(process_instance_key=process_instance_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

        return CancelProcessInstanceResponse()

    async def deploy_resource(
        self, *resource_file_path: str | os.PathLike[str], tenant_id: str | None = None
    ) -> DeployResourceResponse:
        try:
            response = await self._gateway_stub.DeployResource(
                DeployResourceRequest(
                    resources=[await result for result in map(self._create_resource_request, resource_file_path)],
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ProcessInvalidError() from grpc_error
            await self._handle_grpc_error(grpc_error)

        deployments: list[
            DeployResourceResponse.ProcessMetadata
            | DeployResourceResponse.DecisionMetadata
            | DeployResourceResponse.DecisionRequirementsMetadata
            | DeployResourceResponse.FormMetadata
        ] = []
        for deployment in response.deployments:
            metadata_field = deployment.WhichOneof("Metadata")
            metadata = getattr(deployment, metadata_field)
            deployments.append(parse_resource_metadata(metadata_field, metadata))

        return DeployResourceResponse(
            key=response.key,
            deployments=deployments,
            tenant_id=response.tenantId,
        )

    @staticmethod
    async def _create_resource_request(resource_file_path: str | os.PathLike[str]) -> Resource:
        async with await anyio.open_file(resource_file_path, "rb") as file:
            return Resource(name=os.path.basename(resource_file_path), content=await file.read())

    async def evaluate_decision(
        self,
        decision_key: int | None,
        decision_id: str | None,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> EvaluateDecisionResponse:
        if decision_id is None and decision_key is None:
            raise ValueError("decision_key or decision_id must be not None")

        try:
            response = await self._gateway_stub.EvaluateDecision(
                EvaluateDecisionRequest(
                    decisionKey=decision_key,  # type: ignore[arg-type]
                    decisionId=decision_id,  # type: ignore[arg-type]
                    variables=json.dumps(variables),
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT) and (details := grpc_error.details()):
                if "but no decision found for" in details:
                    raise DecisionNotFoundError(decision_id=decision_id, decision_key=decision_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

        return EvaluateDecisionResponse(
            decision_key=response.decisionKey,
            decision_id=response.decisionId,
            decision_name=response.decisionName,
            decision_version=response.decisionVersion,
            decision_requirements_id=response.decisionRequirementsId,
            decision_requirements_key=response.decisionRequirementsKey,
            decision_output=json.loads(response.decisionOutput),
            evaluated_decisions=[
                self._create_evaluated_decision_from_raw(evaluated_decision)
                for evaluated_decision in response.evaluatedDecisions
            ],
            failed_decision_id=response.failedDecisionId,
            failure_message=response.failureMessage,
            tenant_id=response.tenantId,
            decision_instance_key=response.decisionInstanceKey,
        )

    def _create_evaluated_decision_from_raw(
        self, response: EvaluatedDecision
    ) -> EvaluateDecisionResponse.EvaluatedDecision:
        return EvaluateDecisionResponse.EvaluatedDecision(
            decision_key=response.decisionKey,
            decision_id=response.decisionId,
            decision_name=response.decisionName,
            decision_version=response.decisionVersion,
            decision_type=response.decisionType,
            decision_output=json.loads(response.decisionOutput),
            matched_rules=[self._create_matched_rule_from_raw(matched_rule) for matched_rule in response.matchedRules],
            evaluated_inputs=[
                self._create_evaluated_input_from_raw(evaluated_input) for evaluated_input in response.evaluatedInputs
            ],
            tenant_id=response.tenantId,
        )

    def _create_matched_rule_from_raw(
        self, response: MatchedDecisionRule
    ) -> EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule:
        return EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule(
            rule_id=response.ruleId,
            rule_index=response.ruleIndex,
            evaluated_outputs=[
                self._create_evaluated_output_from_raw(evaluated_output)
                for evaluated_output in response.evaluatedOutputs
            ],
        )

    def _create_evaluated_input_from_raw(
        self, response: EvaluatedDecisionInput
    ) -> EvaluateDecisionResponse.EvaluatedDecision.EvaluatedDecisionInput:
        return EvaluateDecisionResponse.EvaluatedDecision.EvaluatedDecisionInput(
            input_id=response.inputId,
            input_name=response.inputName,
            input_value=json.loads(response.inputValue),
        )

    def _create_evaluated_output_from_raw(
        self, response: EvaluatedDecisionOutput
    ) -> EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule.EvaluatedDecisionOutput:
        return EvaluateDecisionResponse.EvaluatedDecision.MatchedDecisionRule.EvaluatedDecisionOutput(
            output_id=response.outputId,
            output_name=response.outputName,
            output_value=json.loads(response.outputValue),
        )

    async def activate_jobs(
        self,
        task_type: str,
        worker: str,
        timeout: int,  # noqa: ASYNC109
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

    async def stream_activate_jobs(
        self,
        task_type: str,
        worker: str,
        timeout: int,  # noqa: ASYNC109
        variables_to_fetch: Iterable[str],
        stream_request_timeout: int,
        tenant_ids: Iterable[str] | None = None,
    ) -> AsyncGenerator[Job]:
        try:
            async for raw_job in self._gateway_stub.StreamActivatedJobs(
                StreamActivatedJobsRequest(
                    type=task_type,
                    worker=worker,
                    timeout=timeout,
                    fetchVariable=variables_to_fetch,
                    tenantIds=tenant_ids or [],
                ),
                timeout=stream_request_timeout,
            ):
                job = self._create_job_from_raw_job(raw_job)
                logger.debug("Got job: %s from zeebe", job)
                yield job
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise StreamActivateJobsRequestInvalidError(task_type, worker, timeout) from grpc_error
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

    async def update_job_timeout(self, job_key: int, timeout: int) -> UpdateJobTimeoutResponse:  # noqa: ASYNC109
        try:
            await self._gateway_stub.UpdateJobTimeout(UpdateJobTimeoutRequest(jobKey=job_key, timeout=timeout))
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFoundError(job_key=job_key) from grpc_error
            elif is_error_status(grpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivatedError(job_key=job_key) from grpc_error
            await self._handle_grpc_error(grpc_error)

        return UpdateJobTimeoutResponse()

    async def broadcast_signal(
        self,
        signal_name: str,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> BroadcastSignalResponse:
        try:
            response = await self._gateway_stub.BroadcastSignal(
                BroadcastSignalRequest(
                    signalName=signal_name,
                    variables=json.dumps(variables),
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            await self._handle_grpc_error(grpc_error)

        return BroadcastSignalResponse(key=response.key, tenant_id=response.tenantId)

    async def publish_message(
        self,
        name: str,
        correlation_key: str,
        time_to_live_in_milliseconds: int,
        variables: Variables,
        message_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PublishMessageResponse:
        try:
            response = await self._gateway_stub.PublishMessage(
                PublishMessageRequest(
                    name=name,
                    correlationKey=correlation_key,
                    messageId=message_id,  # type: ignore[arg-type]
                    timeToLive=time_to_live_in_milliseconds,
                    variables=json.dumps(variables),
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.ALREADY_EXISTS):
                raise MessageAlreadyExistsError() from grpc_error
            await self._handle_grpc_error(grpc_error)

        return PublishMessageResponse(key=response.key, tenant_id=response.tenantId)

    async def topology(self) -> TopologyResponse:
        try:
            response = await self._gateway_stub.Topology(TopologyRequest())
        except grpc.aio.AioRpcError as grpc_error:
            await self._handle_grpc_error(grpc_error)

        return TopologyResponse(
            brokers=[
                TopologyResponse.BrokerInfo(
                    node_id=broker.nodeId,
                    host=broker.host,
                    port=broker.port,
                    partitions=[
                        TopologyResponse.BrokerInfo.Partition(
                            partition_id=partition.partitionId,
                            role=TopologyResponse.BrokerInfo.Partition.PartitionBrokerRole(partition.role),
                            health=TopologyResponse.BrokerInfo.Partition.PartitionBrokerHealth(partition.health),
                        )
                        for partition in broker.partitions
                    ],
                    version=broker.version,
                )
                for broker in response.brokers
            ],
            cluster_size=response.clusterSize,
            partitions_count=response.partitionsCount,
            replication_factor=response.replicationFactor,
            gateway_version=response.gatewayVersion,
        )

    async def healthcheck(self) -> HealthCheckResponse:
        try:
            response = await self._health_stub.Check(HealthCheckRequest(service="gateway_protocol.Gateway"))
        except grpc.aio.AioRpcError as grpc_error:
            pyzeebe_error = self._create_pyzeebe_error_from_grpc_error(grpc_error)
            raise pyzeebe_error from grpc_error

        return HealthCheckResponse(status=response.status)

    def _should_retry(self) -> bool:
        return self._max_connection_retries == -1 or self._current_connection_retries < self._max_connection_retries

    async def _handle_grpc_error(self, grpc_error: grpc.aio.AioRpcError) -> NoReturn:
        try:
            pyzeebe_error = self._create_pyzeebe_error_from_grpc_error(grpc_error)
            raise pyzeebe_error
        except (ZeebeGatewayUnavailableError, ZeebeInternalError, ZeebeDeadlineExceeded):
            self._current_connection_retries += 1
            if not self._should_retry():
                await self._close()
            raise

    async def _close(self) -> None:
        try:
            await self._channel.close()
        except Exception as exception:
            logger.exception("Failed to close channel, %s exception was raised", type(exception).__name__)
        finally:
            self._connected = False

    def _create_pyzeebe_error_from_grpc_error(self, grpc_error: grpc.aio.AioRpcError) -> PyZeebeError:
        if is_error_status(grpc_error, grpc.StatusCode.RESOURCE_EXHAUSTED):
            return ZeebeBackPressureError(grpc_error)
        if is_error_status(grpc_error, grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.CANCELLED):
            return ZeebeGatewayUnavailableError(grpc_error)
        if is_error_status(grpc_error, grpc.StatusCode.INTERNAL):
            return ZeebeInternalError(grpc_error)
        elif is_error_status(grpc_error, grpc.StatusCode.DEADLINE_EXCEEDED):
            return ZeebeDeadlineExceeded(grpc_error)
        return UnknownGrpcStatusCodeError(grpc_error)
