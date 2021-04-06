from random import randint
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from pyzeebe.errors import ProcessDefinitionNotFoundError


def test_run_process(zeebe_client, grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
    assert isinstance(zeebe_client.run_process(
        bpmn_process_id=bpmn_process_id, variables={}, version=version), int)


class TestRunProcessWithResult:
    @pytest.fixture
    def deployed_process(self, grpc_servicer):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
        return bpmn_process_id, version

    def test_run_process_with_result_instance_key_is_int(self, zeebe_client, deployed_process):
        bpmn_process_id, version = deployed_process

        process_instance_key, _ = zeebe_client.run_process_with_result(
            bpmn_process_id, {}, version)

        assert isinstance(process_instance_key, int)

    def test_run_process_with_result_output_variables_are_as_expected(self, zeebe_client, deployed_process):
        expected = {}
        bpmn_process_id, version = deployed_process

        _, output_variables = zeebe_client.run_process_with_result(
            bpmn_process_id, {}, version)

        assert output_variables == expected


def test_deploy_process(zeebe_client):
    zeebe_client.zeebe_adapter.deploy_process = MagicMock()
    file_path = str(uuid4())
    zeebe_client.deploy_process(file_path)
    zeebe_client.zeebe_adapter.deploy_process.assert_called_with(file_path)


def test_run_non_existent_process(zeebe_client):
    with pytest.raises(ProcessDefinitionNotFoundError):
        zeebe_client.run_process(bpmn_process_id=str(uuid4()))


def test_run_non_existent_process_with_result(zeebe_client):
    with pytest.raises(ProcessDefinitionNotFoundError):
        zeebe_client.run_process_with_result(bpmn_process_id=str(uuid4()))


def test_cancel_process_instance(zeebe_client, grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
    process_instance_key = zeebe_client.run_process(
        bpmn_process_id=bpmn_process_id, variables={}, version=version)
    assert isinstance(zeebe_client.cancel_process_instance(
        process_instance_key=process_instance_key), int)


def test_publish_message(zeebe_client):
    zeebe_client.publish_message(
        name=str(uuid4()), correlation_key=str(uuid4()))
