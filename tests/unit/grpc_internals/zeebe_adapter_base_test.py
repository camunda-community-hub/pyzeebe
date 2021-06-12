import grpc
import pytest
from mock import AsyncMock

from pyzeebe.errors import (ZeebeBackPressureError,
                            ZeebeGatewayUnavailableError, ZeebeInternalError)
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase


def test_should_retry_no_current_retries(zeebe_adapter: ZeebeAdapterBase):
    zeebe_adapter._max_connection_retries = 1
    assert zeebe_adapter._should_retry()


def test_should_retry_current_retries_over_max(zeebe_adapter: ZeebeAdapterBase):
    zeebe_adapter._max_connection_retries = 1
    zeebe_adapter._current_connection_retries = 1
    assert not zeebe_adapter._should_retry()


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_internal(zeebe_adapter: ZeebeAdapterBase):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.INTERNAL, None, None
    )
    with pytest.raises(ZeebeInternalError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_back_pressure(zeebe_adapter: ZeebeAdapterBase):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.RESOURCE_EXHAUSTED, None, None
    )
    with pytest.raises(ZeebeBackPressureError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_gateway_unavailable(zeebe_adapter: ZeebeAdapterBase):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.UNAVAILABLE, None, None
    )
    with pytest.raises(ZeebeGatewayUnavailableError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_unkown_error(zeebe_adapter: ZeebeAdapterBase):
    error = grpc.aio.AioRpcError(
        "FakeGrpcStatus", None, None
    )
    with pytest.raises(grpc.aio.AioRpcError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_close_after_retried_unavailable(zeebe_adapter: ZeebeAdapterBase):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.UNAVAILABLE, None, None
    )

    zeebe_adapter._close = AsyncMock()
    zeebe_adapter._max_connection_retries = 1
    with pytest.raises(ZeebeGatewayUnavailableError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)

    zeebe_adapter._close.assert_called_once()


@pytest.mark.asyncio
async def test_close_after_retried_internal(zeebe_adapter: ZeebeAdapterBase):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.INTERNAL, None, None
    )
    zeebe_adapter._close = AsyncMock()
    zeebe_adapter._max_connection_retries = 1
    with pytest.raises(ZeebeInternalError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)

    zeebe_adapter._close.assert_called_once()
