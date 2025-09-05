import abc
import os
from collections.abc import AsyncGenerator, Iterable

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
from pyzeebe.job.job import Job
from pyzeebe.types import Variables


class ZeebeAdapter(abc.ABC):
    """Zeebe adapter.

    This abstract class must be implemented.
    """

    @property
    @abc.abstractmethod
    def connected(self) -> bool: ...

    @property
    @abc.abstractmethod
    def retrying_connection(self) -> bool: ...

    @abc.abstractmethod
    async def create_process_instance(
        self,
        bpmn_process_id: str,
        version: int,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceResponse:
        """Creates and starts an instance of the specified process.

        The process definition to use to create the instance
        can be specified either using its unique key (as returned by DeployProcess),
        or using the BPMN process ID and a version.
        Pass -1 as the version to use the latest deployed version.
        """

    @abc.abstractmethod
    async def create_process_instance_with_result(
        self,
        bpmn_process_id: str,
        version: int,
        variables: Variables,
        timeout: int,  # noqa: ASYNC109
        variables_to_fetch: Iterable[str],
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceWithResultResponse:
        """Similar to CreateProcessInstance RPC,
        creates and starts an instance of the specified process.

        Unlike CreateProcessInstance RPC, the response is returned
        when the process is completed.
        """

    @abc.abstractmethod
    async def cancel_process_instance(self, process_instance_key: int) -> CancelProcessInstanceResponse:
        """Cancels a running process instance."""

    @abc.abstractmethod
    async def deploy_resource(
        self, *resource_file_path: str | os.PathLike[str], tenant_id: str | None = None
    ) -> DeployResourceResponse:
        """Deploys one or more resources (e.g. processes, decision models or forms) to Zeebe.

        Note that this is an atomic call, i.e. either all resources are deployed, or none of them are.
        """

    @abc.abstractmethod
    async def evaluate_decision(
        self,
        decision_key: int | None,
        decision_id: str | None,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> EvaluateDecisionResponse:
        """Evaluates a decision.

        You specify the decision to evaluate either by using its unique KEY
        (as returned by DeployResource), or using the decision ID.
        When using the decision ID, the latest deployed version of the decision is used.
        """

    @abc.abstractmethod
    def activate_jobs(
        self,
        task_type: str,
        worker: str,
        timeout: int,
        max_jobs_to_activate: int,
        variables_to_fetch: Iterable[str],
        request_timeout: int,
        tenant_ids: Iterable[str] | None = None,
    ) -> AsyncGenerator[Job]:
        """Iterates through all known partitions round-robin,
        activates up to the requested maximum,
        and streams them back to the client as they are activated.
        """

    @abc.abstractmethod
    def stream_activate_jobs(
        self,
        task_type: str,
        worker: str,
        timeout: int,
        variables_to_fetch: Iterable[str],
        stream_request_timeout: int,
        tenant_ids: Iterable[str] | None = None,
    ) -> AsyncGenerator[Job]:
        """Opens a long living stream for the given job type, worker name, job timeout, and fetch variables.

        This will cause available jobs in the engine to be activated and pushed down this stream.
        """

    @abc.abstractmethod
    async def complete_job(self, job_key: int, variables: Variables) -> CompleteJobResponse:
        """Completes a job with the given payload, which allows completing the associated service task."""

    @abc.abstractmethod
    async def fail_job(
        self, job_key: int, retries: int, message: str, retry_back_off_ms: int, variables: Variables
    ) -> FailJobResponse:
        """Marks the job as failed.

        If the retries argument is positive and no retry back off is set,
        the job is immediately activatable again.
        If the retry back off is positive the job becomes activatable once
        the back off timeout has passed. If the retries argument is zero or negative,
        an incident is raised, tagged with the given errorMessage,
        and the job is not activatable until the incident is resolved.
        If the variables argument is set, the variables are merged into the process
        at the local scope of the job's associated task.
        """

    @abc.abstractmethod
    async def throw_error(
        self, job_key: int, message: str, variables: Variables, error_code: str = ""
    ) -> ThrowErrorResponse:
        """ThrowError reports a business error (i.e. non-technical)
        that occurs while processing a job.

        The error is handled in the process by an error catch event.
        If there is no error catch event with the specified errorCode,
        an incident is raised instead.

        Variables can be passed along with the thrown error to provide
        additional details that can be used in the process.
        """

    @abc.abstractmethod
    async def update_job_timeout(self, job_key: int, timeout: int) -> UpdateJobTimeoutResponse:
        """Updates the deadline of a job using the timeout (in milliseconds) provided.

        This can be used for extending or shortening the job deadline.
        The new deadline will be calculated from the current time, adding the timeout provided.
        """

    @abc.abstractmethod
    async def broadcast_signal(
        self,
        signal_name: str,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> BroadcastSignalResponse:
        """Broadcasts a signal."""

    @abc.abstractmethod
    async def publish_message(
        self,
        name: str,
        correlation_key: str,
        time_to_live_in_milliseconds: int,
        variables: Variables,
        message_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PublishMessageResponse:
        """Publishes a single message.

        Messages are published to specific partitions computed from their correlation keys.
        """

    @abc.abstractmethod
    async def topology(self) -> TopologyResponse:
        """Obtains the current topology of the cluster the gateway is part of."""

    @abc.abstractmethod
    async def healthcheck(self) -> HealthCheckResponse: ...
