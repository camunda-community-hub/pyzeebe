import json
from typing import List, Generator, Dict

from grpc import Channel

from pyz.grpc_internals.zeebe_pb2 import *
from pyz.grpc_internals.zeebe_pb2_grpc import GatewayStub
from pyz.task.job_context import JobContext


class ZeebeAdapter:
    def __init__(self, channel: Channel):
        self.gateway_stub = GatewayStub(channel)

    def activate_jobs(self, task_type: str, worker: str, timeout: int, max_jobs_to_activate: int,
                      variables_to_fetch: List[str], request_timeout: int) -> Generator[JobContext, None, None]:
        for response in self.gateway_stub.ActivateJobs(
                ActivateJobsRequest(type=task_type, worker=worker, timeout=timeout,
                                    maxJobsToActivate=max_jobs_to_activate,
                                    fetchVariable=variables_to_fetch, requestTimeout=request_timeout)):
            for job in response.jobs:
                yield self._create_task_context_from_job(job)

    @staticmethod
    def _create_task_context_from_job(job) -> JobContext:
        return JobContext(key=job.key, _type=job.type,
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

    def complete_job(self, job_key: int, variables: Dict) -> None:
        self.gateway_stub.CompleteJob(CompleteJobRequest(jobKey=job_key, variables=json.dumps(variables)))

    def fail_job(self, job_key: int, error_code: str, message: str):
        self.gateway_stub.FailJob(FailJobRequest(jobKey=job_key, errorCode=error_code, errorMessage=message))

    def throw_error(self, job_key: int, error_code: str, message: str):
        self.gateway_stub.ThrowError(ThrowErrorRequest(jobKey=job_key, errorCode=error_code, errorMessage=message))

    def create_workflow_instance(self, bpmn_process_id: str, version: int, variables: Dict) -> str:
        response = self.gateway_stub.CreateWorkflowInstance(
            CreateWorkflowInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                          variables=json.dumps(variables))).result()
        return response.workflowInstanceKey

    def create_workflow_instance_with_result(self, bpmn_process_id: str, version: int, variables: Dict,
                                             timeout: int, variables_to_fetch) -> Dict:
        response = self.gateway_stub.CreateWorkflowInstanceWithResult(
            CreateWorkflowInstanceWithResultRequest(
                CreateWorkflowInstanceRequest(bpmnProcessId=bpmn_process_id, version=version,
                                              variables=json.dumps(variables))),
            requestTimeout=timeout, fetchVariables=variables_to_fetch).result()
        return json.loads(response.variables)

    def publish_message(self, name: str, correlation_key: str, time_to_live_in_milliseconds: int,
                        variables: Dict) -> None:
        self.gateway_stub.PublishMessage(
            PublishMessageRequest(name=name, correlationKey=correlation_key, timeToLive=time_to_live_in_milliseconds,
                                  variables=json.dumps(variables)))
