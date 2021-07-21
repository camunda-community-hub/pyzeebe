from uuid import uuid4

import grpc
import pytest
from mock import AsyncMock

from pyzeebe import SyncZeebeClient
from pyzeebe.errors import ProcessDefinitionNotFoundError
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter

# Pytest doesn't play well with loop.run_until_complete unless the test has a
# running asyncio loop
pytestmark = pytest.mark.asyncio


@pytest.fixture
def sync_zeebe_client(aio_grpc_channel: grpc.aio.Channel) -> SyncZeebeClient:
    client = SyncZeebeClient(aio_grpc_channel)
    return client


class TestRunProcess:
    def test_run_process_returns_int(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process

        process_instance_key = sync_zeebe_client.run_process(
            bpmn_process_id, version=version
        )

        assert isinstance(process_instance_key, int)

    def test_raises_process_definition_not_found_error_for_invalid_process_id(self, sync_zeebe_client: SyncZeebeClient):
        with pytest.raises(ProcessDefinitionNotFoundError):
            sync_zeebe_client.run_process(bpmn_process_id=str(uuid4()))


class TestRunProcessWithResult:
    def test_run_process_with_result_instance_key_is_int(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process

        process_instance_key, _ = sync_zeebe_client.run_process_with_result(
            bpmn_process_id, {}, version
        )

        assert isinstance(process_instance_key, int)

    def test_run_process_with_result_output_variables_are_as_expected(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        expected = {}
        bpmn_process_id, version = deployed_process

        _, output_variables = sync_zeebe_client.run_process_with_result(
            bpmn_process_id, {}, version
        )

        assert output_variables == expected

    def test_raises_process_definition_not_found_error_for_invalid_process_id(self, sync_zeebe_client: SyncZeebeClient):
        with pytest.raises(ProcessDefinitionNotFoundError):
            sync_zeebe_client.run_process_with_result(
                bpmn_process_id=str(uuid4())
            )


class TestCancelProcessInstance:
    def test_cancel_process_instance(self, sync_zeebe_client: SyncZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process
        process_instance_key = sync_zeebe_client.run_process(
            bpmn_process_id=bpmn_process_id, variables={}, version=version
        )

        returned_process_instance_key = sync_zeebe_client.cancel_process_instance(
            process_instance_key
        )

        assert returned_process_instance_key == process_instance_key


class TestDeployProcess:
    def test_calls_deploy_process_of_zeebe_adapter(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.zeebe_adapter.deploy_process = AsyncMock()
        file_path = str(uuid4())

        sync_zeebe_client.deploy_process(file_path)

        sync_zeebe_client.zeebe_adapter.deploy_process.assert_called_with(
            file_path
        )


class TestPublishMessage:
    def test_calls_publish_message_of_zeebe_adapter(self, sync_zeebe_client: SyncZeebeClient):
        sync_zeebe_client.zeebe_adapter.publish_message = AsyncMock()
        name = str(uuid4())
        correlation_key = str(uuid4())

        sync_zeebe_client.publish_message(name, correlation_key)

        sync_zeebe_client.zeebe_adapter.publish_message.assert_called_once()
