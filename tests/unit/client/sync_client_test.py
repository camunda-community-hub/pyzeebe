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
def sync_zeebe_client(event_loop, aio_grpc_channel: grpc.aio.Channel) -> SyncZeebeClient:
    # NOTE: event_loop: pytest doesn't play well with loop.run_until_complete unless the test has a
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


class TestDeployProcess:
    def test_calls_deploy_process_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.deploy_process = AsyncMock()
        file_path = str(uuid4())

        sync_zeebe_client.deploy_process(file_path)

        sync_zeebe_client.client.deploy_process.assert_called_with(file_path)


class TestDeployResource:
    def test_calls_deploy_resource_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.deploy_resource = AsyncMock()
        file_path = str(uuid4())

        sync_zeebe_client.deploy_resource(file_path)

        sync_zeebe_client.client.deploy_resource.assert_called_with(file_path, tenant_id=None)


class TestPublishMessage:
    def test_calls_publish_message_of_zeebe_client(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.client.publish_message = AsyncMock()
        name = str(uuid4())
        correlation_key = str(uuid4())

        sync_zeebe_client.publish_message(name, correlation_key)

        sync_zeebe_client.client.publish_message.assert_called_once()
