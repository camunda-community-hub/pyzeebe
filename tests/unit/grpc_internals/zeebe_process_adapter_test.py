from random import randint
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import grpc
import pytest

from pyzeebe.errors import (
    DecisionNotFoundError,
    InvalidJSONError,
    ProcessDefinitionHasNoStartEventError,
    ProcessDefinitionNotFoundError,
    ProcessInstanceNotFoundError,
    ProcessInvalidError,
    ProcessTimeoutError,
)
from pyzeebe.grpc_internals.types import (
    CreateProcessInstanceResponse,
    CreateProcessInstanceWithResultResponse,
    DeployResourceResponse,
    EvaluateDecisionResponse,
)
from pyzeebe.grpc_internals.zeebe_process_adapter import ZeebeProcessAdapter
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.random_utils import RANDOM_RANGE


@pytest.fixture(autouse=True)
def mocked_aiofiles_open():
    read_mock = AsyncMock(return_value=b"")

    file_mock = AsyncMock()
    file_mock.__aenter__.return_value.read = read_mock

    with patch("pyzeebe.grpc_internals.zeebe_process_adapter.anyio.open_file", return_value=file_mock) as open_mock:
        yield open_mock


@pytest.mark.anyio
class TestCreateProcessInstance:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])

        response = await zeebe_adapter.create_process_instance(bpmn_process_id, version, {})

        assert isinstance(response, CreateProcessInstanceResponse)

    async def test_raises_on_unkown_process(self, zeebe_adapter: ZeebeProcessAdapter):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)

        with pytest.raises(ProcessDefinitionNotFoundError):
            await zeebe_adapter.create_process_instance(bpmn_process_id, version, {})

    async def test_raises_on_invalid_json(self, zeebe_adapter: ZeebeProcessAdapter):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)

        error = grpc.aio.AioRpcError(grpc.StatusCode.INVALID_ARGUMENT, None, None)
        zeebe_adapter._gateway_stub.CreateProcessInstance = AsyncMock(side_effect=error)

        with pytest.raises(InvalidJSONError):
            await zeebe_adapter.create_process_instance(bpmn_process_id, version, None)

    async def test_raises_on_no_start_event(self, zeebe_adapter: ZeebeProcessAdapter):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        error = grpc.aio.AioRpcError(grpc.StatusCode.FAILED_PRECONDITION, None, None)
        zeebe_adapter._gateway_stub.CreateProcessInstance = AsyncMock(side_effect=error)

        with pytest.raises(ProcessDefinitionHasNoStartEventError):
            await zeebe_adapter.create_process_instance(bpmn_process_id, version, {})


@pytest.mark.anyio
class TestCreateProcessWithResult:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])

        response = await zeebe_adapter.create_process_instance_with_result(
            bpmn_process_id=bpmn_process_id,
            variables={},
            version=version,
            timeout=0,
            variables_to_fetch=[],
            tenant_id=None,
        )

        assert isinstance(response, CreateProcessInstanceWithResultResponse)

    async def test_process_instance_key_type_is_int(
        self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock
    ):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])

        response = await zeebe_adapter.create_process_instance_with_result(
            bpmn_process_id=bpmn_process_id,
            variables={},
            version=version,
            timeout=0,
            variables_to_fetch=[],
            tenant_id=None,
        )

        assert isinstance(response.process_instance_key, int)

    async def test_variables_type_is_dict(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])

        response = await zeebe_adapter.create_process_instance_with_result(
            bpmn_process_id=bpmn_process_id,
            variables={},
            version=version,
            timeout=0,
            variables_to_fetch=[],
            tenant_id=None,
        )

        assert isinstance(response.variables, dict)

    async def test_raises_on_process_timeout(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)

        error = grpc.aio.AioRpcError(grpc.StatusCode.DEADLINE_EXCEEDED, None, None)

        zeebe_adapter._gateway_stub.CreateProcessInstanceWithResult = AsyncMock(side_effect=error)

        with pytest.raises(ProcessTimeoutError):
            await zeebe_adapter.create_process_instance_with_result(
                bpmn_process_id,
                variables={},
                version=version,
                timeout=0,
                variables_to_fetch=[],
                tenant_id=None,
            )


@pytest.mark.anyio
class TestCancelProcess:
    async def test_cancels_the_process(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
        response = await zeebe_adapter.create_process_instance(
            bpmn_process_id=bpmn_process_id, variables={}, version=version
        )

        await zeebe_adapter.cancel_process_instance(response.process_instance_key)

        assert response.process_instance_key not in grpc_servicer.active_processes.keys()

    async def test_raises_on_already_cancelled_process(
        self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock
    ):
        error = grpc.aio.AioRpcError(grpc.StatusCode.NOT_FOUND, None, None)

        zeebe_adapter._gateway_stub.CancelProcessInstance = AsyncMock(side_effect=error)

        with pytest.raises(ProcessInstanceNotFoundError):
            await zeebe_adapter.cancel_process_instance(process_instance_key=randint(0, RANDOM_RANGE))


@pytest.mark.anyio
class TestDeployResource:
    async def test_deploy_process_response_type(self, zeebe_adapter: ZeebeProcessAdapter):
        file_path = str(uuid4()) + ".bpmn"

        response = await zeebe_adapter.deploy_resource(file_path)

        assert isinstance(response, DeployResourceResponse)
        assert isinstance(response.deployments[0], DeployResourceResponse.ProcessMetadata)

    async def test_deploy_decision_response_type(self, zeebe_adapter: ZeebeProcessAdapter):
        file_path = str(uuid4()) + ".dmn"

        response = await zeebe_adapter.deploy_resource(file_path)

        assert isinstance(response, DeployResourceResponse)
        assert isinstance(response.deployments[0], DeployResourceResponse.DecisionMetadata)

    async def test_deploy_form_response_type(self, zeebe_adapter: ZeebeProcessAdapter):
        file_path = str(uuid4()) + ".form"

        response = await zeebe_adapter.deploy_resource(file_path)

        assert isinstance(response, DeployResourceResponse)
        assert isinstance(response.deployments[0], DeployResourceResponse.FormMetadata)

    async def test_raises_on_invalid_process(self, zeebe_adapter: ZeebeProcessAdapter):
        error = grpc.aio.AioRpcError(grpc.StatusCode.INVALID_ARGUMENT, None, None)

        zeebe_adapter._gateway_stub.DeployResource = AsyncMock(side_effect=error)

        with pytest.raises(ProcessInvalidError):
            await zeebe_adapter.deploy_resource()

    async def test_calls_open_in_rb_mode(self, zeebe_adapter: ZeebeProcessAdapter, mocked_aiofiles_open):
        file_path = str(uuid4())

        await zeebe_adapter.deploy_resource(file_path)

        mocked_aiofiles_open.assert_called_with(file_path, "rb")


@pytest.mark.anyio
class TestEvaluateDecision:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        decision_id = str(uuid4())
        decision_key = randint(0, 10)
        grpc_servicer.mock_deploy_decision(decision_key, decision_id)

        response = await zeebe_adapter.evaluate_decision(decision_key, decision_id, {})

        assert isinstance(response, EvaluateDecisionResponse)

    async def test_raises_on_unkown_process(self, zeebe_adapter: ZeebeProcessAdapter):
        decision_id = str(uuid4())
        decision_key = randint(0, 10)

        with pytest.raises(DecisionNotFoundError):
            await zeebe_adapter.evaluate_decision(decision_key, decision_id, {})
