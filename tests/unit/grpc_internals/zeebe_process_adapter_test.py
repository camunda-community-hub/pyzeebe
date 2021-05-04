from io import BytesIO
from random import randint
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import grpc
import pytest

from pyzeebe.errors import (InvalidJSONError,
                            ProcessDefinitionHasNoStartEventError,
                            ProcessDefinitionNotFoundError,
                            ProcessInstanceNotFoundError, ProcessInvalidError)
from pyzeebe.grpc_internals.zeebe_process_adapter import ZeebeProcessAdapter
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.grpc_utils import GRPCStatusCode
from tests.unit.utils.random_utils import RANDOM_RANGE


@pytest.mark.asyncio
class TestCreateProcessInstance:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])

        response = await zeebe_adapter.create_process_instance(
            bpmn_process_id, version, {}
        )

        assert isinstance(response, int)

    async def test_raises_on_unkown_process(self, zeebe_adapter: ZeebeProcessAdapter):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)

        with pytest.raises(ProcessDefinitionNotFoundError):
            await zeebe_adapter.create_process_instance(bpmn_process_id, version, {})

    async def test_raises_on_invalid_json(self, zeebe_adapter: ZeebeProcessAdapter):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)

        error = grpc.aio.AioRpcError(
            grpc.StatusCode.INVALID_ARGUMENT, None, None
        )
        zeebe_adapter._gateway_stub.CreateProcessInstance = AsyncMock(
            side_effect=error
        )

        with pytest.raises(InvalidJSONError):
            await zeebe_adapter.create_process_instance(bpmn_process_id, version, None)

    async def test_raises_on_no_start_event(self, zeebe_adapter: ZeebeProcessAdapter):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        error = grpc.aio.AioRpcError(
            grpc.StatusCode.FAILED_PRECONDITION, None, None
        )
        zeebe_adapter._gateway_stub.CreateProcessInstance = AsyncMock(
            side_effect=error
        )

        with pytest.raises(ProcessDefinitionHasNoStartEventError):
            await zeebe_adapter.create_process_instance(bpmn_process_id, version, {})


@pytest.mark.asyncio
class TestCreateProcessWithResult:
    async def test_process_instance_key_type_is_int(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])

        process_instance_key, _ = await zeebe_adapter.create_process_instance_with_result(
            bpmn_process_id=bpmn_process_id,
            variables={},
            version=version,
            timeout=0,
            variables_to_fetch=[]
        )

        assert isinstance(process_instance_key, int)

    async def test_variables_type_is_dict(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])

        _, response = await zeebe_adapter.create_process_instance_with_result(
            bpmn_process_id=bpmn_process_id,
            variables={},
            version=version,
            timeout=0,
            variables_to_fetch=[]
        )

        assert isinstance(response, dict)


@pytest.mark.asyncio
class TestCancelProcess:
    async def test_cancels_the_process(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        bpmn_process_id = str(uuid4())
        version = randint(0, 10)
        grpc_servicer.mock_deploy_process(bpmn_process_id, version, [])
        process_instance_key = await zeebe_adapter.create_process_instance(
            bpmn_process_id=bpmn_process_id,
            variables={},
            version=version
        )

        await zeebe_adapter.cancel_process_instance(process_instance_key)

        assert process_instance_key not in grpc_servicer.active_processes.keys()

    async def test_raises_on_already_cancelled_process(self, zeebe_adapter: ZeebeProcessAdapter, grpc_servicer: GatewayMock):
        error = grpc.aio.AioRpcError(
            grpc.StatusCode.NOT_FOUND, None, None
        )

        zeebe_adapter._gateway_stub.CancelProcessInstance = AsyncMock(
            side_effect=error
        )

        with pytest.raises(ProcessInstanceNotFoundError):
            await zeebe_adapter.cancel_process_instance(
                process_instance_key=randint(0, RANDOM_RANGE)
            )


@pytest.mark.asyncio
class TestDeployProcess:
    async def test_raises_on_invalid_process(self, zeebe_adapter: ZeebeProcessAdapter):
        with patch("builtins.open") as mock_open:
            mock_open.return_value = BytesIO()

            error = grpc.aio.AioRpcError(
                grpc.StatusCode.INVALID_ARGUMENT, None, None
            )

            zeebe_adapter._gateway_stub.DeployProcess = AsyncMock(
                side_effect=error
            )

            with pytest.raises(ProcessInvalidError):
                await zeebe_adapter.deploy_process()

    async def test_calls_open_in_rb_mode(self, zeebe_adapter: ZeebeProcessAdapter):
        with patch("builtins.open") as mock_open:
            mock_open.return_value = BytesIO()
            file_path = str(uuid4())
            await zeebe_adapter.deploy_process(file_path)
            mock_open.assert_called_with(file_path, "rb")
