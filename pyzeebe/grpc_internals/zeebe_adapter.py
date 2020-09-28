import json
import logging
import os.path
from typing import List, Generator, Dict

import grpc

from pyzeebe.common.exceptions import *
from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.grpc_internals.zeebe_pb2 import *
from pyzeebe.grpc_internals.zeebe_pb2_grpc import GatewayStub
from pyzeebe.job.job import Job


class ZeebeAdapter(object):
    def __init__(self, hostname: str = None, port: int = None, credentials: BaseCredentials = None,
                 channel: grpc.Channel = None, secure_connection: bool = False):
        if channel:
            self.connection_uri = None
            self._channel = channel
        else:
            self.connection_uri = self._get_connection_uri(hostname, port, credentials)
            self._channel = self._create_channel(self.connection_uri, credentials, secure_connection)

        self.secure_connection = secure_connection
        self.connected = False
        self.retrying_connection = True
        self._channel.subscribe(self._check_connectivity, try_to_connect=True)
        self.gateway_stub = GatewayStub(self._channel)

    @staticmethod
    def _get_connection_uri(hostname: str = None, port: int = None, credentials: BaseCredentials = None) -> str:
        if credentials and credentials.get_connection_uri():
            return credentials.get_connection_uri()
        if hostname or port:
            return f"{hostname or 'localhost'}:{port or 26500}"
        else:
            return os.getenv("ZEEBE_ADDRESS", "localhost:26500")

    @staticmethod
    def _create_channel(connection_uri: str, credentials: BaseCredentials = None,
                        secure_connection: bool = False) -> grpc.Channel:
        if credentials:
            return grpc.secure_channel(connection_uri, credentials.grpc_credentials)
        elif secure_connection:
            return grpc.secure_channel(connection_uri, grpc.ssl_channel_credentials())
        else:
            return grpc.insecure_channel(connection_uri)

    def _check_connectivity(self, value: grpc.ChannelConnectivity) -> None:
        logging.debug(f"Grpc channel connectivity changed to: {value}")
        if value in [grpc.ChannelConnectivity.READY, grpc.ChannelConnectivity.IDLE]:
            logging.debug(f"Connected to {self.connection_uri or 'zeebe'}")
            self.connected = True
            self.retrying_connection = False
        elif value == grpc.ChannelConnectivity.CONNECTING:
            logging.debug(f"Connecting to {self.connection_uri or 'zeebe'}.")
            self.connected = False
            self.retrying_connection = True
        elif value == grpc.ChannelConnectivity.TRANSIENT_FAILURE:
            logging.warning(f"Lost connection to {self.connection_uri or 'zeebe'}. Retrying...")
            self.connected = False
            self.retrying_connection = True
        elif value == grpc.ChannelConnectivity.SHUTDOWN:
            logging.error(f"Failed to establish connection to {self.connection_uri or 'zeebe'}. Non recoverable")
            self.connected = False
            self.retrying_connection = False
            raise ConnectionAbortedError(f"Lost connection to {self.connection_uri or 'zeebe'}")

    def activate_jobs(self, task_type: str, worker: str, timeout: int, max_jobs_to_activate: int,
                      variables_to_fetch: List[str], request_timeout: int) -> Generator[Job, None, None]:
        try:
            for response in self.gateway_stub.ActivateJobs(
                    ActivateJobsRequest(type=task_type, worker=worker, timeout=timeout,
                                        maxJobsToActivate=max_jobs_to_activate,
                                        fetchVariable=variables_to_fetch, requestTimeout=request_timeout)):
                for job in response.jobs:
                    job = self._create_job_from_response(job)
                    logging.debug(f"Got job: {job} from zeebe")
                    yield job
        except grpc.RpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.INVALID_ARGUMENT):
                raise ActivateJobsRequestInvalid(task_type, worker, timeout, max_jobs_to_activate)
            else:
                self._common_zeebe_grpc_errors(rpc_error)

    def _create_job_from_response(self, response) -> Job:
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
        with open(workflow_file_path, "rb") as file:
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
