import json
from random import randint
from typing import List, Dict
from unittest.mock import patch
from uuid import uuid4

import grpc
from zeebe_grpc.gateway_pb2 import *
from zeebe_grpc.gateway_pb2_grpc import GatewayServicer

from pyzeebe.job.job import Job
from pyzeebe.job.job_status import JobStatus
from pyzeebe.task.task import Task
from tests.unit.utils.random_utils import RANDOM_RANGE, random_job


@patch("grpc.insecure_channel")
def mock_channel():
    pass


class GatewayMock(GatewayServicer):
    # TODO: Mock behaviour of zeebe

    def __init__(self):
        self.deployed_workflows = {}
        self.active_workflows = {}
        self.active_jobs: Dict[int, Job] = {}
        self.messages = {}

    def ActivateJobs(self, request, context):
        if not request.type:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ActivateJobsResponse()

        if request.maxJobsToActivate <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ActivateJobsResponse()

        if request.timeout <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ActivateJobsResponse()

        if not request.worker:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ActivateJobsResponse()

        jobs = []
        for active_job in self.active_jobs.values():
            if active_job.type == request.type:
                jobs.append(ActivatedJob(key=active_job.key, type=active_job.type,
                                         workflowInstanceKey=active_job.workflow_instance_key,
                                         bpmnProcessId=active_job.bpmn_process_id,
                                         workflowDefinitionVersion=active_job.workflow_definition_version,
                                         workflowKey=active_job.workflow_key,
                                         elementId=active_job.element_id,
                                         elementInstanceKey=active_job.element_instance_key,
                                         customHeaders=json.dumps(active_job.custom_headers),
                                         worker=active_job.worker, retries=active_job.retries,
                                         deadline=active_job.deadline,
                                         variables=json.dumps(active_job.variables)))
        yield ActivateJobsResponse(jobs=jobs)

    def CompleteJob(self, request, context):
        if request.jobKey in self.active_jobs.keys():
            active_job = self.active_jobs.get(request.jobKey)
            self.handle_job(active_job, JobStatus.Completed, context)
            return CompleteJobResponse()
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CompleteJobResponse()

    def FailJob(self, request, context):
        if request.jobKey in self.active_jobs.keys():
            active_job = self.active_jobs.get(request.jobKey)
            self.handle_job(active_job, JobStatus.Failed, context)
            return FailJobResponse()
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return FailJobResponse()

    def ThrowError(self, request, context):
        if request.jobKey in self.active_jobs.keys():
            active_job = self.active_jobs.get(request.jobKey)
            self.handle_job(active_job, JobStatus.ErrorThrown, context)
            return CompleteJobResponse()
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CompleteJobResponse()

    @staticmethod
    def handle_job(job: Job, status_on_deactivate: JobStatus, context):
        if job.status != JobStatus.Running:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
        else:
            job.status = status_on_deactivate
        return context

    def CreateWorkflowInstance(self, request, context):
        if request.bpmnProcessId in self.deployed_workflows.keys():
            for task in self.deployed_workflows[request.bpmnProcessId]["tasks"]:
                job = random_job(task)
                self.active_jobs[job.key] = job

            workflow_instance_key = randint(0, RANDOM_RANGE)
            self.active_workflows[workflow_instance_key] = request.bpmnProcessId
            return CreateWorkflowInstanceResponse(workflowKey=randint(0, RANDOM_RANGE),
                                                  bpmnProcessId=request.bpmnProcessId,
                                                  version=request.version, workflowInstanceKey=workflow_instance_key)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CreateWorkflowInstanceResponse()

    def CreateWorkflowInstanceWithResult(self, request, context):
        if request.request.bpmnProcessId in self.deployed_workflows.keys():
            workflow_instance_key = randint(0, RANDOM_RANGE)
            self.active_workflows[workflow_instance_key] = request.request.bpmnProcessId

            return CreateWorkflowInstanceWithResultResponse(workflowKey=request.request.workflowKey,
                                                            workflowInstanceKey=workflow_instance_key,
                                                            bpmnProcessId=request.request.bpmnProcessId,
                                                            version=randint(0, 10), variables=request.request.variables)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CreateWorkflowInstanceWithResultResponse()

    def CancelWorkflowInstance(self, request, context):
        if request.workflowInstanceKey in self.active_workflows.keys():
            del self.active_workflows[request.workflowInstanceKey]
            return CancelWorkflowInstanceResponse()
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CancelWorkflowInstanceResponse()

    def DeployWorkflow(self, request, context):
        workflows = []
        for workflow in request.workflows:
            workflow_metadata = WorkflowMetadata(bpmnProcessId=str(uuid4()), version=randint(0, 10),
                                                 workflowKey=randint(0, RANDOM_RANGE), resourceName=workflow.name)
            workflows.append(workflow_metadata)

        return DeployWorkflowResponse(key=randint(0, RANDOM_RANGE), workflows=workflows)

    def PublishMessage(self, request, context):
        if request.messageId in self.messages.keys():
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
        else:
            self.messages[request.messageId] = request.correlationKey
        return PublishMessageResponse()

    def mock_deploy_workflow(self, bpmn_process_id: str, version: int, tasks: List[Task]):
        self.deployed_workflows[bpmn_process_id] = {"bpmn_process_id": bpmn_process_id, "version": version,
                                                    "tasks": tasks}
