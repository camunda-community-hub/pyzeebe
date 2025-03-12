from __future__ import annotations

import asyncio
import os

import grpc

from pyzeebe import ZeebeClient
from pyzeebe.grpc_internals.types import (
    BroadcastSignalResponse,
    CancelProcessInstanceResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    DeployResourceResponse,
    EvaluateDecisionResponse,
    HealthCheckResponse,
    PublishMessageResponse,
    TopologyResponse,
)
from pyzeebe.types import Variables


class SyncZeebeClient:
    def __init__(self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = 10) -> None:
        self.loop = asyncio.get_event_loop()
        self.client = ZeebeClient(grpc_channel, max_connection_retries)

    def run_process(
        self,
        bpmn_process_id: str,
        variables: Variables | None = None,
        version: int = -1,
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceResponse:
        return self.loop.run_until_complete(self.client.run_process(bpmn_process_id, variables, version, tenant_id))

    run_process.__doc__ = ZeebeClient.publish_message.__doc__

    def run_process_with_result(
        self,
        bpmn_process_id: str,
        variables: Variables | None = None,
        version: int = -1,
        timeout: int = 0,
        variables_to_fetch: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> CreateProcessInstanceWithResultResponse:
        return self.loop.run_until_complete(
            self.client.run_process_with_result(
                bpmn_process_id, variables, version, timeout, variables_to_fetch, tenant_id
            )
        )

    run_process_with_result.__doc__ = ZeebeClient.publish_message.__doc__

    def cancel_process_instance(self, process_instance_key: int) -> CancelProcessInstanceResponse:
        return self.loop.run_until_complete(self.client.cancel_process_instance(process_instance_key))

    cancel_process_instance.__doc__ = ZeebeClient.cancel_process_instance.__doc__

    def deploy_resource(
        self, *resource_file_path: str | os.PathLike[str], tenant_id: str | None = None
    ) -> DeployResourceResponse:
        return self.loop.run_until_complete(self.client.deploy_resource(*resource_file_path, tenant_id=tenant_id))

    deploy_resource.__doc__ = ZeebeClient.deploy_resource.__doc__

    def evaluate_decision(
        self,
        decision_key: int | None,
        decision_id: str | None,
        variables: Variables | None = None,
        tenant_id: str | None = None,
    ) -> EvaluateDecisionResponse:
        return self.loop.run_until_complete(
            self.client.evaluate_decision(decision_key, decision_id, variables=variables, tenant_id=tenant_id)
        )

    evaluate_decision.__doc__ = ZeebeClient.evaluate_decision.__doc__

    def broadcast_signal(
        self,
        signal_name: str,
        variables: Variables | None = None,
        tenant_id: str | None = None,
    ) -> BroadcastSignalResponse:
        return self.loop.run_until_complete(
            self.client.broadcast_signal(
                signal_name,
                variables,
                tenant_id,
            )
        )

    broadcast_signal.__doc__ = ZeebeClient.broadcast_signal.__doc__

    def publish_message(
        self,
        name: str,
        correlation_key: str,
        variables: Variables | None = None,
        time_to_live_in_milliseconds: int = 60000,
        message_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PublishMessageResponse:
        return self.loop.run_until_complete(
            self.client.publish_message(
                name,
                correlation_key,
                variables,
                time_to_live_in_milliseconds,
                message_id,
                tenant_id,
            )
        )

    publish_message.__doc__ = ZeebeClient.publish_message.__doc__

    def topology(self) -> TopologyResponse:
        return self.loop.run_until_complete(self.client.topology())

    topology.__doc__ = ZeebeClient.topology.__doc__

    def healthcheck(self) -> HealthCheckResponse:
        return self.loop.run_until_complete(self.client.healthcheck())

    healthcheck.__doc__ = ZeebeClient.healthcheck.__doc__
