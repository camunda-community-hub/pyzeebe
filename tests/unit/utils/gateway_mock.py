import json
from random import randint
from unittest.mock import patch
from uuid import uuid4

import grpc

from pyzeebe.job.job import Job
from pyzeebe.job.job_status import JobStatus
from pyzeebe.proto.gateway_pb2 import (
    ActivatedJob,
    ActivateJobsResponse,
    BroadcastSignalResponse,
    CancelProcessInstanceResponse,
    CompleteJobResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    DecisionMetadata,
    Deployment,
    DeployResourceResponse,
    EvaluatedDecision,
    EvaluatedDecisionInput,
    EvaluatedDecisionOutput,
    EvaluateDecisionRequest,
    EvaluateDecisionResponse,
    FailJobResponse,
    FormMetadata,
    MatchedDecisionRule,
    ProcessMetadata,
    PublishMessageResponse,
    TopologyResponse,
    UpdateJobTimeoutResponse,
)
from pyzeebe.proto.gateway_pb2_grpc import GatewayServicer
from pyzeebe.task.task import Task
from tests.unit.utils.random_utils import RANDOM_RANGE, random_job


@patch("grpc.insecure_channel")
def mock_channel():
    pass


class GatewayMock(GatewayServicer):
    # TODO: Mock behaviour of zeebe

    def __init__(self):
        self.deployed_processes = {}
        self.deployed_decisions = {}
        self.active_processes = {}
        self.active_jobs: dict[int, Job] = {}
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
                jobs.append(
                    ActivatedJob(
                        key=active_job.key,
                        type=active_job.type,
                        processInstanceKey=active_job.process_instance_key,
                        bpmnProcessId=active_job.bpmn_process_id,
                        processDefinitionVersion=active_job.process_definition_version,
                        processDefinitionKey=active_job.process_definition_key,
                        elementId=active_job.element_id,
                        elementInstanceKey=active_job.element_instance_key,
                        customHeaders=json.dumps(active_job.custom_headers),
                        worker=active_job.worker,
                        retries=active_job.retries,
                        deadline=active_job.deadline,
                        variables=json.dumps(active_job.variables),
                        tenantId=active_job.tenant_id,
                    )
                )
        yield ActivateJobsResponse(jobs=jobs)

    def StreamActivatedJobs(self, request, context):
        if not request.type:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ActivatedJob()

        if request.timeout <= 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ActivatedJob()

        if not request.worker:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return ActivatedJob()

        for active_job in self.active_jobs.values():
            if active_job.type == request.type:
                yield ActivatedJob(
                    key=active_job.key,
                    type=active_job.type,
                    processInstanceKey=active_job.process_instance_key,
                    bpmnProcessId=active_job.bpmn_process_id,
                    processDefinitionVersion=active_job.process_definition_version,
                    processDefinitionKey=active_job.process_definition_key,
                    elementId=active_job.element_id,
                    elementInstanceKey=active_job.element_instance_key,
                    customHeaders=json.dumps(active_job.custom_headers),
                    worker=active_job.worker,
                    retries=active_job.retries,
                    deadline=active_job.deadline,
                    variables=json.dumps(active_job.variables),
                )

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
            job._set_status(status_on_deactivate)
        return context

    def UpdateJobTimeout(self, request, context):
        if request.jobKey in self.active_jobs.keys():
            active_job = self.active_jobs[request.jobKey]
            if active_job.status != JobStatus.Running:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            return UpdateJobTimeoutResponse()
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return UpdateJobTimeoutResponse()

    def CreateProcessInstance(self, request, context):
        if request.bpmnProcessId in self.deployed_processes.keys():
            for task in self.deployed_processes[request.bpmnProcessId]["tasks"]:
                job = random_job(task)
                self.active_jobs[job.key] = job

            process_instance_key = randint(0, RANDOM_RANGE)
            self.active_processes[process_instance_key] = request.bpmnProcessId
            return CreateProcessInstanceResponse(
                processDefinitionKey=randint(0, RANDOM_RANGE),
                bpmnProcessId=request.bpmnProcessId,
                version=request.version,
                processInstanceKey=process_instance_key,
                tenantId=request.tenantId,
            )
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CreateProcessInstanceResponse()

    def CreateProcessInstanceWithResult(self, request, context):
        if request.request.bpmnProcessId in self.deployed_processes.keys():
            process_instance_key = randint(0, RANDOM_RANGE)
            self.active_processes[process_instance_key] = request.request.bpmnProcessId

            return CreateProcessInstanceWithResultResponse(
                processDefinitionKey=request.request.processDefinitionKey,
                processInstanceKey=process_instance_key,
                bpmnProcessId=request.request.bpmnProcessId,
                version=randint(0, 10),
                variables=request.request.variables,
                tenantId=request.request.tenantId,
            )
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CreateProcessInstanceWithResultResponse()

    def CancelProcessInstance(self, request, context):
        if request.processInstanceKey in self.active_processes.keys():
            del self.active_processes[request.processInstanceKey]
            return CancelProcessInstanceResponse()
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return CancelProcessInstanceResponse()

    def DeployResource(self, request, context):
        resources = []
        for resource in request.resources:
            if resource.name.endswith("bpmn"):
                metadata = Deployment(
                    process=ProcessMetadata(
                        bpmnProcessId=str(uuid4()),
                        version=randint(0, 10),
                        processDefinitionKey=randint(0, RANDOM_RANGE),
                        resourceName=resource.name,
                        tenantId=request.tenantId,
                    )
                )
                resources.append(metadata)
            elif resource.name.endswith("dmn"):
                metadata = Deployment(
                    decision=DecisionMetadata(
                        dmnDecisionId=str(uuid4()),
                        dmnDecisionName=resource.name,
                        version=randint(0, 10),
                        decisionKey=randint(0, RANDOM_RANGE),
                        dmnDecisionRequirementsId=str(uuid4()),
                        decisionRequirementsKey=randint(0, RANDOM_RANGE),
                        tenantId=request.tenantId,
                    )
                )
                resources.append(metadata)
            elif resource.name.endswith("form"):
                metadata = Deployment(
                    form=FormMetadata(
                        formId=str(uuid4()),
                        version=randint(0, 10),
                        formKey=randint(0, RANDOM_RANGE),
                        resourceName=resource.name,
                        tenantId=request.tenantId,
                    )
                )
                resources.append(metadata)

        return DeployResourceResponse(key=randint(0, RANDOM_RANGE), deployments=resources, tenantId=request.tenantId)

    def EvaluateDecision(self, request, context):
        if request.decisionId in self.deployed_decisions:
            return EvaluateDecisionResponse(
                decisionKey=request.decisionKey,
                decisionId=request.decisionId,
                decisionName="test",
                decisionVersion=randint(0, 10),
                decisionRequirementsId="test",
                decisionRequirementsKey=randint(0, 10),
                decisionOutput='{"foo": "bar"}',
                evaluatedDecisions=[
                    EvaluatedDecision(
                        decisionKey=request.decisionKey,
                        decisionId=request.decisionId,
                        decisionName="test",
                        decisionVersion=randint(0, 10),
                        decisionType="test",
                        decisionOutput='{"foo": "bar"}',
                        matchedRules=[
                            MatchedDecisionRule(
                                ruleId="test",
                                ruleIndex=randint(0, 10),
                                evaluatedOutputs=[
                                    EvaluatedDecisionOutput(
                                        outputId="test",
                                        outputName="test",
                                        outputValue='"test"',
                                    )
                                ],
                            )
                        ],
                        evaluatedInputs=[
                            EvaluatedDecisionInput(
                                inputId="test",
                                inputName=name,
                                inputValue=value,
                            )
                            for name, value in json.loads(request.variables).items()
                        ],
                        tenantId=request.tenantId,
                    )
                ],
                failedDecisionId="",
                failureMessage="",
                tenantId=request.tenantId,
                decisionInstanceKey=randint(0, 10),
            )
        else:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(
                f"Command 'EVALUATE' rejected with code 'INVALID_ARGUMENT': "
                f"Expected to evaluate decision '{request.decisionId}', but no decision found for id '{request.decisionId}'"
            )
            return EvaluateDecisionResponse()

    def BroadcastSignal(self, request, context):
        return BroadcastSignalResponse()

    def PublishMessage(self, request, context):
        if request.messageId in self.messages.keys():
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
        else:
            self.messages[request.messageId] = request.correlationKey
        return PublishMessageResponse()

    def mock_deploy_process(self, bpmn_process_id: str, version: int, tasks: list[Task]):
        self.deployed_processes[bpmn_process_id] = {
            "bpmn_process_id": bpmn_process_id,
            "version": version,
            "tasks": tasks,
        }

    def mock_deploy_decision(self, decision_key: int, decision_id: str):
        self.deployed_decisions[decision_id] = {
            "decision_id": decision_id,
            "decision_key": decision_key,
        }

    def Topology(self, request, context):
        return TopologyResponse()
