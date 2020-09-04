import json
import logging
import os.path
from typing import List, Generator, Dict

import grpc

from pyzeebe.common.exceptions import *
from pyzeebe.grpc_internals.zeebe_pb2 import *
from pyzeebe.grpc_internals.zeebe_pb2_grpc import GatewayStub
from pyzeebe.task.task_context import TaskContext


class ZeebeAdapter(object):
    def __init__(self, hostname: str = None, port: int = None, channel: grpc.Channel = None, **kwargs):
        if channel:
            self._channel = channel
            self.connection_uri = None
        else:
            if hostname or port:
                self.connection_uri = f'{hostname or "localhost"}:{port or 26500}'
            else:
                self.connection_uri = os.getenv('ZEEBE_ADDRESS', 'localhost:26500')
            self._channel = grpc.insecure_channel(self.connection_uri)

        self.connected = False
        self.retrying_connection = True
        self._channel.subscribe(self._check_connectivity, try_to_connect=True)
        self.gateway_stub = GatewayStub(self._channel)

    def _check_connectivity(self, value: grpc.ChannelConnectivity) -> None:
        logging.debug(f'Grpc channel connectivity changed to: {value}')
        if value in [grpc.ChannelConnectivity.READY, grpc.ChannelConnectivity.IDLE]:
            logging.debug('Connected to Zeebe')
            self.connected = True
            self.retrying_connection = False
        elif value in [grpc.ChannelConnectivity.CONNECTING, grpc.ChannelConnectivity.TRANSIENT_FAILURE]:
            logging.warning('No connection to Zeebe, recoverable. Reconnecting...')
            self.connected = False
            self.retrying_connection = True
        elif value == grpc.ChannelConnectivity.SHUTDOWN:
            logging.error('Failed to establish connection to Zeebe. Non recoverable')
            self.connected = False
            self.retrying_connection = False
            raise ConnectionAbortedError(f'Lost connection to {self.connection_uri}')

    def activate_jobs(self, task_type: str, worker: str, timeout: int, max_jobs_to_activate: int,
                      variables_to_fetch: List[str], request_timeout: int) -> Generator[TaskContext, None, None]:
        try:
            for response in self.gateway_stub.ActivateJobs(
                    ActivateJobsRequest(type=task_type, worker=worker, timeout=timeout,
                                        maxJobsToActivate=max_jobs_to_activate,
                                        fetchVariable=variables_to_fetch, requestTimeout=request_timeout)):
                for job in response.jobs:
                    context = self._create_task_context_from_job(job)
                    logging.debug(f'Got job: {context} from zeebe')
                    yield context
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ActivateJobsRequestInvalid(task_type, worker, timeout, max_jobs_to_activate)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    @staticmethod
    def _create_task_context_from_job(job) -> TaskContext:
        return TaskContext(key=job.key, _type=job.type,
                           workflow_instance_key=job.workflowInstanceKey,
                           bpmn_process_id=job.bpmnProcessId,
                           workflow_definition_version=job.workflowDefinitionVersion,
                           workflow_key=job.workflowKey,
                           element_id=job.elementId,
                           element_instance_key=job.elementInstanceKey,
                           custom_headers=json.loads(job.customHeaders),
                           worker=job.worker,
                           retries=job.retries,
                           deadline=job.deadline,
                           variables=json.loads(job.variables))

    def complete_job(self, job_key: int, variables: Dict) -> CompleteJobResponse:
        try:
            return self.gateway_stub.CompleteJob(CompleteJobRequest(jobKey=job_key, variables=json.dumps(variables)))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFound(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivated(job_key=job_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def fail_job(self, job_key: int, message: str) -> FailJobResponse:
        try:
            return self.gateway_stub.FailJob(FailJobRequest(jobKey=job_key, errorMessage=message))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFound(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivated(job_key=job_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def throw_error(self, job_key: int, message: str) -> ThrowErrorResponse:
        try:
            return self.gateway_stub.ThrowError(
                ThrowErrorRequest(jobKey=job_key, errorMessage=message))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise JobNotFound(job_key=job_key)
            elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
                raise JobAlreadyDeactivated(job_key=job_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def create_workflow_instance(self, bpmn_process_id: str, version: int, variables: Dict) -> int:
        try:
            response = self.gateway_stub.CreateWorkflowInstance(
                CreateWorkflowInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                              variables=json.dumps(variables)))
            return response.workflowInstanceKey
        except grpc.RpcError as rpc_error:
            self._create_workflow_errors(rpc_error, bpmn_process_id, version, variables)

    def create_workflow_instance_with_result(self, bpmn_process_id: str, version: int, variables: Dict,
                                             timeout: int, variables_to_fetch) -> Dict:
        try:
            response = self.gateway_stub.CreateWorkflowInstanceWithResult(
                CreateWorkflowInstanceWithResultRequest(
                    request=CreateWorkflowInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                                          variables=json.dumps(variables)),
                    requestTimeout=timeout, fetchVariables=variables_to_fetch))
            return json.loads(response.variables)
        except grpc.RpcError as rpc_error:
            self._create_workflow_errors(rpc_error, bpmn_process_id, version, variables)

    def _create_workflow_errors(self, rpc_error: grpc.RpcError, bpmn_process_id: str, version: int,
                                variables: Dict) -> None:
        if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
            raise WorkflowNotFound(bpmn_process_id=bpmn_process_id, version=version)
        elif self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
            raise InvalidJSON(
                f"Cannot start workflow: {bpmn_process_id} with version {version}. Variables: {variables}")
        elif self.is_error_status(rpc_error, grpc.StatusCode.FAILED_PRECONDITION):
            raise WorkflowHasNoStartEvent(bpmn_process_id=bpmn_process_id)
        else:
            self._common_zeebe_grpc_errors(rpc_error)

    def cancel_workflow_instance(self, workflow_instance_key: int) -> None:
        try:
            self.gateway_stub.CancelWorkflowInstance(
                CancelWorkflowInstanceRequest(workflowInstanceKey=workflow_instance_key))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.NOT_FOUND):
                raise WorkflowInstanceNotFound(workflow_instance_key=workflow_instance_key)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def publish_message(self, name: str, correlation_key: str, time_to_live_in_milliseconds: int,
                        variables: Dict) -> PublishMessageResponse:
        try:
            return self.gateway_stub.PublishMessage(
                PublishMessageRequest(name=name, correlationKey=correlation_key,
                                      timeToLive=time_to_live_in_milliseconds,
                                      variables=json.dumps(variables)))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.ALREADY_EXISTS):
                raise MessageAlreadyExists()
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def deploy_workflow(self, *workflow_file_path: str) -> DeployWorkflowResponse:

        try:
            return self.gateway_stub.DeployWorkflow(
                DeployWorkflowRequest(workflows=map(self._get_workflow_request_object, workflow_file_path)))
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise WorkflowInvalid()
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    @staticmethod
    def _get_workflow_request_object(workflow_file_path: str) -> WorkflowRequestObject:
        with open(workflow_file_path, 'rb') as file:
            return WorkflowRequestObject(name=os.path.split(workflow_file_path)[-1],
                                         definition=file.read())

    def _common_zeebe_grpc_errors(self, rpc_error: grpc.RpcError):
        if self.is_error_status(rpc_error, grpc.StatusCode.RESOURCE_EXHAUSTED):
            raise ZeebeBackPressure()
        elif self.is_error_status(rpc_error, grpc.StatusCode.UNAVAILABLE):
            raise ZeebeGatewayUnavailable()
        elif self.is_error_status(rpc_error, grpc.StatusCode.INTERNAL):
            raise ZeebeInternalError()
        else:
            raise rpc_error

    @staticmethod
    def is_error_status(rpc_error: grpc.RpcError, status_code: grpc.StatusCode):
        return rpc_error._state.code == status_code
