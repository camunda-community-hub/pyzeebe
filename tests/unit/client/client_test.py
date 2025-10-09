from random import randint
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient
from pyzeebe.errors import ProcessDefinitionNotFoundError
from pyzeebe.grpc_internals.types import (
    CancelProcessInstanceResponse,
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    EvaluateDecisionResponse,
)
from tests.unit.utils.gateway_mock import GatewayMock


@pytest.mark.anyio
async def test_run_process(zeebe_client: ZeebeClient, grpc_servicer: GatewayMock):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
    assert isinstance(
        await zeebe_client.run_process(bpmn_process_id=bpmn_process_id, variables={}, version=version),
        CreateProcessInstanceResponse,
    )


@pytest.mark.anyio
class TestRunProcessWithResult:
    async def test_run_process_with_result_type(self, zeebe_client: ZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process

        response = await zeebe_client.run_process_with_result(bpmn_process_id, {}, version)

        assert isinstance(response, CreateProcessInstanceWithResultResponse)

    async def test_run_process_with_result_instance_key_is_int(self, zeebe_client: ZeebeClient, deployed_process):
        bpmn_process_id, version = deployed_process

        response = await zeebe_client.run_process_with_result(bpmn_process_id, {}, version)

        assert isinstance(response.process_instance_key, int)

    async def test_run_process_with_result_output_variables_are_as_expected(
        self, zeebe_client: ZeebeClient, deployed_process
    ):
        expected = {}
        bpmn_process_id, version = deployed_process

        response = await zeebe_client.run_process_with_result(bpmn_process_id, {}, version)

        assert response.variables == expected


@pytest.mark.anyio
async def test_deploy_resource(zeebe_client: ZeebeClient):
    zeebe_client.zeebe_adapter.deploy_resource = AsyncMock()
    file_path = str(uuid4())
    await zeebe_client.deploy_resource(file_path)
    zeebe_client.zeebe_adapter.deploy_resource.assert_called_with(file_path, tenant_id=None)


@pytest.mark.anyio
async def test_run_non_existent_process(zeebe_client: ZeebeClient):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process(bpmn_process_id=str(uuid4()))


@pytest.mark.anyio
async def test_run_non_existent_process_with_result(zeebe_client: ZeebeClient):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process_with_result(bpmn_process_id=str(uuid4()))


@pytest.mark.anyio
async def test_cancel_process_instance(zeebe_client: ZeebeClient, grpc_servicer: GatewayMock):
    bpmn_process_id = str(uuid4())
    version = randint(0, 10)
    grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
    response = await zeebe_client.run_process(bpmn_process_id=bpmn_process_id, variables={}, version=version)
    assert isinstance(
        await zeebe_client.cancel_process_instance(process_instance_key=response.process_instance_key),
        CancelProcessInstanceResponse,
    )


@pytest.mark.anyio
async def test_evaluate_decision(zeebe_client: ZeebeClient, grpc_servicer: GatewayMock):
    decision_id = str(uuid4())
    decision_key = randint(0, 10)
    grpc_servicer.mock_deploy_decision(decision_key, decision_id)
    assert isinstance(
        await zeebe_client.evaluate_decision(decision_key, decision_id),
        EvaluateDecisionResponse,
    )


@pytest.mark.anyio
async def test_broadcast_signal(zeebe_client: ZeebeClient):
    await zeebe_client.broadcast_signal(signal_name=str(uuid4()))


@pytest.mark.anyio
async def test_publish_message(zeebe_client: ZeebeClient):
    await zeebe_client.publish_message(name=str(uuid4()), correlation_key=str(uuid4()))


@pytest.mark.anyio
async def test_topology(zeebe_client: ZeebeClient):
    await zeebe_client.topology()


@pytest.mark.xfail(reason="Required GRPC health checking stubs")
@pytest.mark.anyio
async def test_healthcheck(zeebe_client: ZeebeClient):
    await zeebe_client.healthcheck()
