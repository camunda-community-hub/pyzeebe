from random import randint
from uuid import uuid4

import pytest
from mock import AsyncMock

from pyzeebe.errors import ProcessDefinitionNotFoundError


@pytest.mark.asyncio
async def test_run_process(zeebe_client, grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
    assert isinstance(await zeebe_client.run_process(
        bpmn_process_id=bpmn_process_id, variables={}, version=version), int)


@pytest.mark.asyncio
class TestRunProcessWithResult:
    async def test_run_process_with_result_instance_key_is_int(self, zeebe_client, deployed_process):
        bpmn_process_id, version = deployed_process

        process_instance_key, _ = await zeebe_client.run_process_with_result(
            bpmn_process_id, {}, version
        )

        assert isinstance(process_instance_key, int)

    async def test_run_process_with_result_output_variables_are_as_expected(self, zeebe_client, deployed_process):
        expected = {}
        bpmn_process_id, version = deployed_process

        _, output_variables = await zeebe_client.run_process_with_result(
            bpmn_process_id, {}, version
        )

        assert output_variables == expected


@pytest.mark.asyncio
async def test_deploy_process(zeebe_client):
    zeebe_client.zeebe_adapter.deploy_process = AsyncMock()
    file_path = str(uuid4())
    await zeebe_client.deploy_process(file_path)
    zeebe_client.zeebe_adapter.deploy_process.assert_called_with(file_path)


@pytest.mark.asyncio
async def test_run_non_existent_process(zeebe_client):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process(bpmn_process_id=str(uuid4()))


@pytest.mark.asyncio
async def test_run_non_existent_process_with_result(zeebe_client):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process_with_result(bpmn_process_id=str(uuid4()))


@pytest.mark.asyncio
async def test_cancel_process_instance(zeebe_client, grpc_servicer):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
    process_instance_key = await zeebe_client.run_process(
        bpmn_process_id=bpmn_process_id, variables={}, version=version)
    assert isinstance(await zeebe_client.cancel_process_instance(process_instance_key=process_instance_key), int)


@pytest.mark.asyncio
async def test_publish_message(zeebe_client):
    await zeebe_client.publish_message(name=str(uuid4()), correlation_key=str(uuid4()))
