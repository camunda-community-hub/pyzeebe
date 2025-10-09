from unittest.mock import AsyncMock

import grpc
import pytest

from pyzeebe.errors import (
    ZeebeBackPressureError,
    ZeebeDeadlineExceeded,
    ZeebeGatewayUnavailableError,
    ZeebeInternalError,
)
from pyzeebe.errors.zeebe_errors import UnknownGrpcStatusCodeError
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase


@pytest.mark.anyio
class TestShouldRetry:
    async def test_returns_true_when_no_current_retries(self, zeebe_adapter: ZeebeAdapterBase):
        zeebe_adapter._max_connection_retries = 1
        assert zeebe_adapter._should_retry()

    async def test_returns_false_when_current_retries_over_max(self, zeebe_adapter: ZeebeAdapterBase):
        zeebe_adapter._max_connection_retries = 1
        zeebe_adapter._current_connection_retries = 1
        assert not zeebe_adapter._should_retry()


@pytest.mark.anyio
class TestHandleRpcError:
    async def test_raises_internal_error_on_internal_error_status(self, zeebe_adapter: ZeebeAdapterBase):
        error = grpc.aio.AioRpcError(grpc.StatusCode.INTERNAL, None, None)
        with pytest.raises(ZeebeInternalError) as err:
            await zeebe_adapter._handle_grpc_error(error)

        assert (
            str(err.value)
            == "ZeebeInternalError(grpc_error=AioRpcError(code=StatusCode.INTERNAL, details=None, debug_error_string=None))"
        )

    async def test_raises_back_pressure_error_on_resource_exhausted(self, zeebe_adapter: ZeebeAdapterBase):
        error = grpc.aio.AioRpcError(grpc.StatusCode.RESOURCE_EXHAUSTED, None, None)
        with pytest.raises(ZeebeBackPressureError) as err:
            await zeebe_adapter._handle_grpc_error(error)

        assert (
            str(err.value)
            == "ZeebeBackPressureError(grpc_error=AioRpcError(code=StatusCode.RESOURCE_EXHAUSTED, details=None, debug_error_string=None))"
        )

    async def test_raises_deadline_exceeded_on_deadline_exceeded(self, zeebe_adapter: ZeebeAdapterBase):
        error = grpc.aio.AioRpcError(grpc.StatusCode.DEADLINE_EXCEEDED, None, None)
        with pytest.raises(ZeebeDeadlineExceeded) as err:
            await zeebe_adapter._handle_grpc_error(error)

        assert (
            str(err.value)
            == "ZeebeDeadlineExceeded(grpc_error=AioRpcError(code=StatusCode.DEADLINE_EXCEEDED, details=None, debug_error_string=None))"
        )

    async def test_raises_gateway_unavailable_on_unavailable_status(
        self,
        zeebe_adapter: ZeebeAdapterBase,
    ):
        error = grpc.aio.AioRpcError(grpc.StatusCode.UNAVAILABLE, None, None)
        with pytest.raises(ZeebeGatewayUnavailableError) as err:
            await zeebe_adapter._handle_grpc_error(error)

        assert (
            str(err.value)
            == "ZeebeGatewayUnavailableError(grpc_error=AioRpcError(code=StatusCode.UNAVAILABLE, details=None, debug_error_string=None))"
        )

    async def test_raises_gateway_unavailable_on_cancelled_status(
        self,
        zeebe_adapter: ZeebeAdapterBase,
    ):
        error = grpc.aio.AioRpcError(grpc.StatusCode.CANCELLED, None, None)

        with pytest.raises(ZeebeGatewayUnavailableError) as err:
            await zeebe_adapter._handle_grpc_error(error)

        assert (
            str(err.value)
            == "ZeebeGatewayUnavailableError(grpc_error=AioRpcError(code=StatusCode.CANCELLED, details=None, debug_error_string=None))"
        )

    async def test_raises_unkown_grpc_status_code_on_unkown_status_code(
        self,
        zeebe_adapter: ZeebeAdapterBase,
    ):
        error = grpc.aio.AioRpcError("FakeGrpcStatus", None, None)
        with pytest.raises(UnknownGrpcStatusCodeError) as err:
            await zeebe_adapter._handle_grpc_error(error)

        assert (
            str(err.value)
            == "UnknownGrpcStatusCodeError(grpc_error=AioRpcError(code=FakeGrpcStatus, details=None, debug_error_string=None))"
        )

    async def test_closes_after_retries_exceeded(self, zeebe_adapter: ZeebeAdapterBase):
        error = grpc.aio.AioRpcError(grpc.StatusCode.UNAVAILABLE, None, None)

        zeebe_adapter._channel.close = AsyncMock()
        zeebe_adapter._max_connection_retries = 1
        with pytest.raises(ZeebeGatewayUnavailableError):
            await zeebe_adapter._handle_grpc_error(error)

        assert zeebe_adapter.connected is False
        zeebe_adapter._channel.close.assert_awaited_once()

    async def test_closes_after_internal_error(self, zeebe_adapter: ZeebeAdapterBase):
        error = grpc.aio.AioRpcError(grpc.StatusCode.INTERNAL, None, None)

        zeebe_adapter._channel.close = AsyncMock()
        zeebe_adapter._max_connection_retries = 1
        with pytest.raises(ZeebeInternalError):
            await zeebe_adapter._handle_grpc_error(error)

        assert zeebe_adapter.connected is False
        zeebe_adapter._channel.close.assert_awaited_once()
