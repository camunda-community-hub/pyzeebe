from random import randint
from mock import MagicMock, patch, AsyncMock
from uuid import uuid4

import grpc
import pytest

from pyzeebe.credentials.camunda_cloud_credentials import \
    CamundaCloudCredentials
from pyzeebe.credentials.oauth_credentials import OAuthCredentials
from pyzeebe.errors import (ZeebeBackPressureError,
                            ZeebeGatewayUnavailableError, ZeebeInternalError)
from pyzeebe.grpc_internals.zeebe_adapter_base import (ZeebeAdapterBase,
                                                       create_channel,
                                                       create_connection_uri)
from tests.unit.utils.random_utils import RANDOM_RANGE


def test_should_retry_no_current_retries(zeebe_adapter):
    zeebe_adapter._max_connection_retries = 1
    assert zeebe_adapter._should_retry()


def test_should_retry_current_retries_over_max(zeebe_adapter):
    zeebe_adapter._max_connection_retries = 1
    zeebe_adapter._current_connection_retries = 1
    assert not zeebe_adapter._should_retry()


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_internal(zeebe_adapter):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.INTERNAL, None, None
    )
    with pytest.raises(ZeebeInternalError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_back_pressure(zeebe_adapter):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.RESOURCE_EXHAUSTED, None, None
    )
    with pytest.raises(ZeebeBackPressureError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_gateway_unavailable(zeebe_adapter):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.UNAVAILABLE, None, None
    )
    with pytest.raises(ZeebeGatewayUnavailableError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_common_zeebe_grpc_error_unkown_error(zeebe_adapter):
    error = grpc.aio.AioRpcError(
        "FakeGrpcStatus", None, None
    )
    with pytest.raises(grpc.aio.AioRpcError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)


@pytest.mark.asyncio
async def test_close_after_retried_unavailable(zeebe_adapter):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.UNAVAILABLE, None, None
    )

    zeebe_adapter._close = AsyncMock()
    zeebe_adapter._max_connection_retries = 1
    with pytest.raises(ZeebeGatewayUnavailableError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)

    zeebe_adapter._close.assert_called_once()


@pytest.mark.asyncio
async def test_close_after_retried_internal(zeebe_adapter):
    error = grpc.aio.AioRpcError(
        grpc.StatusCode.INTERNAL, None, None
    )
    zeebe_adapter._close = AsyncMock()
    zeebe_adapter._max_connection_retries = 1
    with pytest.raises(ZeebeInternalError):
        await zeebe_adapter._common_zeebe_grpc_errors(error)

    zeebe_adapter._close.assert_called_once()


class TestCreateChannel:
    def test_creates_insecure_channel_on_default(self):
        with patch("grpc.aio.insecure_channel") as channel_mock:
            create_channel(str(uuid4()))

            channel_mock.assert_called_once()

    def test_creates_secure_channel_when_given_credentials(self):
        with patch("grpc.aio.secure_channel") as channel_mock:
            create_channel(str(uuid4()), credentials=MagicMock())

            channel_mock.assert_called_once()

    def test_creates_secure_channel_when_secure_connection_is_enabled(self):
        with patch("grpc.aio.secure_channel") as channel_mock:
            create_channel(str(uuid4()), secure_connection=True)

            channel_mock.assert_called_once()


class TestCreateConnectionUri:
    def test_uses_credentials_first(self):
        credentials = MagicMock(return_value=str(uuid4()))

        connection_uri = create_connection_uri(
            credentials=credentials, hostname="localhost", port=123
        )

        assert connection_uri == credentials.get_connection_uri()

    def test_uses_hostname_and_port_when_given(self):
        hostname = str(uuid4())
        port = randint(0, 10000)

        connection_uri = create_connection_uri(hostname, port)

        assert connection_uri == f"{hostname}:{port}"

    def test_default_port_value_is_26500(self):
        hostname = str(uuid4())

        connection_uri = create_connection_uri(hostname)

        assert connection_uri == f"{hostname}:26500"

    def test_default_hostname_is_localhost(self):
        port = randint(0, 10000)

        connection_uri = create_connection_uri(port=port)

        assert connection_uri == f"localhost:{port}"

    def test_default_values_are_taken_from_env_variables(self):
        address = f"{str(uuid4())}:{randint(0, 10000)}"
        with patch("os.getenv", return_value=address):
            connection_uri = create_connection_uri()

            assert connection_uri == address
