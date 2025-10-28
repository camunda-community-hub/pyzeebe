from unittest.mock import AsyncMock
from uuid import uuid4

import grpc
import pytest

from pyzeebe import SyncZeebeClient
from pyzeebe.errors import ProcessDefinitionNotFoundError
from pyzeebe.grpc_internals.types import (
    CancelProcessInstanceResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
)


@pytest.fixture
def sync_zeebe_client(anyio_backend, aio_grpc_channel: grpc.aio.Channel) -> SyncZeebeClient:
    # NOTE: anyio_backend: pytest doesn't play well with loop.run_until_complete unless the test has a
    # running asyncio loop
    client = SyncZeebeClient(aio_grpc_channel)
    return client


class TestRunProcess:
    def test_run_process_returns(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process

        response = sync_zeebe_client.run_process(bpmn_process_id, version=version)

        assert isinstance(response, CreateProcessInstanceResponse)

    def test_raises_process_definition_not_found_error_for_invalid_process_id(self, sync_zeebe_client: SyncZeebeClient):
        with pytest.raises(ProcessDefinitionNotFoundError):
            sync_zeebe_client.run_process(bpmn_process_id=str(uuid4()))


class TestRunProcessWithResult:
    def test_run_process_with_result_returns(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process

        response = sync_zeebe_client.run_process_with_result(bpmn_process_id, {}, version)

        assert isinstance(response, CreateProcessInstanceWithResultResponse)

    def test_run_process_returns_int(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process

        response = sync_zeebe_client.run_process(bpmn_process_id, version=version)

        assert isinstance(response.process_instance_key, int)

    def test_run_process_with_result_output_variables_are_as_expected(
        self, sync_zeebe_client: SyncZeebeClient, deployed_process
    ):
        expected = {}
        bpmn_process_id, version = deployed_process

        response = sync_zeebe_client.run_process_with_result(bpmn_process_id, {}, version)

        assert response.variables == expected

    def test_raises_process_definition_not_found_error_for_invalid_process_id(self, sync_zeebe_client: SyncZeebeClient):
        with pytest.raises(ProcessDefinitionNotFoundError):
            sync_zeebe_client.run_process_with_result(bpmn_process_id=str(uuid4()))


class TestCancelProcessInstance:
    def test_cancel_process_instance(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process
        response = sync_zeebe_client.run_process(bpmn_process_id=bpmn_process_id, variables={}, version=version)

        cancel_response = sync_zeebe_client.cancel_process_instance(response.process_instance_key)

        assert isinstance(cancel_response, CancelProcessInstanceResponse)


class TestDeployResource:
    def test_calls_deploy_resource_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.deploy_resource = AsyncMock()
        file_path = str(uuid4())

        sync_zeebe_client.deploy_resource(file_path)

        sync_zeebe_client.client.deploy_resource.assert_called_with(file_path, tenant_id=None)


class TestEvaluateDecision:
    def test_calls_evaluate_decision_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.evaluate_decision = AsyncMock()
        decision_id = str(uuid4())

        sync_zeebe_client.evaluate_decision(decision_key=None, decision_id=decision_id)

        sync_zeebe_client.client.evaluate_decision.assert_called_with(None, decision_id, variables=None, tenant_id=None)


class TestBroadcastSignal:
    def test_calls_broadcast_signal_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.broadcast_signal = AsyncMock()
        name = str(uuid4())

        sync_zeebe_client.broadcast_signal(name)

        sync_zeebe_client.client.broadcast_signal.assert_called_once()


class TestPublishMessage:
    def test_calls_publish_message_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.publish_message = AsyncMock()
        name = str(uuid4())
        correlation_key = str(uuid4())

        sync_zeebe_client.publish_message(name, correlation_key)

        sync_zeebe_client.client.publish_message.assert_called_once()


class TestTopology:
    def test_calls_topology_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.topology = AsyncMock()

        sync_zeebe_client.topology()

        sync_zeebe_client.client.topology.assert_called_once()


class TestHealthCheck:
    def test_calls_topology_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.healthcheck = AsyncMock()

        sync_zeebe_client.healthcheck()

        sync_zeebe_client.client.healthcheck.assert_called_once()
