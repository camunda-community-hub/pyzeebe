from random import randint
from unittest.mock import patch, MagicMock
from uuid import uuid4

import grpc
import pytest

from pyzeebe.credentials.camunda_cloud_credentials import CamundaCloudCredentials
from pyzeebe.credentials.oauth_credentials import OAuthCredentials
from pyzeebe.exceptions import ZeebeBackPressure, ZeebeGatewayUnavailable, ZeebeInternalError
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from tests.unit.utils.grpc_utils import GRPCStatusCode
from tests.unit.utils.random_utils import RANDOM_RANGE


def test_connectivity_ready(zeebe_adapter):
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.READY)
    assert not zeebe_adapter.retrying_connection
    assert zeebe_adapter.connected


def test_connectivity_transient_idle(zeebe_adapter):
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.IDLE)
    assert not zeebe_adapter.retrying_connection
    assert zeebe_adapter.connected


def test_connectivity_connecting(zeebe_adapter):
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.CONNECTING)
    assert zeebe_adapter.retrying_connection
    assert not zeebe_adapter.connected


def test_connectivity_transient_failure_retry(zeebe_adapter):
    zeebe_adapter._max_connection_retries = 1
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.TRANSIENT_FAILURE)
    assert zeebe_adapter.retrying_connection
    assert not zeebe_adapter.connected


def test_connectivity_transient_failure_no_retry(zeebe_adapter):
    zeebe_adapter._max_connection_retries = 0
    zeebe_adapter._channel.close = MagicMock()
    with pytest.raises(ConnectionAbortedError):
        zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.TRANSIENT_FAILURE)
        zeebe_adapter._channel.close.assert_called_once()


def test_connectivity_transient_failure_logs_warning(caplog, zeebe_adapter):
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.TRANSIENT_FAILURE)
    expected_logger = "pyzeebe.grpc_internals.zeebe_adapter_base"
    expected_level = "WARNING"
    matching_logs = [
        log
        for log in caplog.records
        if log.name == expected_logger and log.levelname == expected_level
    ]
    assert len(matching_logs) > 0


def test_connectivity_shutdown(zeebe_adapter):
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.SHUTDOWN)
    assert not zeebe_adapter.connected
    assert not zeebe_adapter.retrying_connection


def test_should_retry_no_current_retries(zeebe_adapter):
    zeebe_adapter._max_connection_retries = 1
    assert zeebe_adapter._should_retry()


def test_should_retry_current_retries_over_max(zeebe_adapter):
    zeebe_adapter._max_connection_retries = 1
    zeebe_adapter._current_connection_retries = 1
    assert not zeebe_adapter._should_retry()


def test_only_port(zeebe_adapter):
    port = randint(0, 10000)
    zeebe_adapter = ZeebeAdapterBase(port=port)
    assert zeebe_adapter.connection_uri == f"localhost:{port}"


def test_only_host(zeebe_adapter):
    hostname = str(uuid4())
    zeebe_adapter = ZeebeAdapterBase(hostname=hostname)
    assert zeebe_adapter.connection_uri == f"{hostname}:26500"


def test_host_and_port(zeebe_adapter):
    hostname = str(uuid4())
    port = randint(0, 10000)
    zeebe_adapter = ZeebeAdapterBase(hostname=hostname, port=port)
    assert zeebe_adapter.connection_uri == f"{hostname}:{port}"


def test_with_secure_connection(zeebe_adapter):
    with patch("grpc.secure_channel") as grpc_secure_channel_mock:
        ZeebeAdapterBase(secure_connection=True)
        grpc_secure_channel_mock.assert_called()


def test_with_camunda_cloud_credentials(zeebe_adapter):
    CamundaCloudCredentials.get_access_token = MagicMock(return_value=str(uuid4()))
    credentials = CamundaCloudCredentials(str(uuid4()), str(uuid4()), str(uuid4()))

    with patch("grpc.secure_channel") as grpc_secure_channel_mock:
        ZeebeAdapterBase(credentials=credentials)
        grpc_secure_channel_mock.assert_called()


def test_credentials_connection_uri_gotten(zeebe_adapter):
    client_id = str(uuid4())
    client_secret = str(uuid4())
    cluster_id = str(uuid4())
    CamundaCloudCredentials.get_access_token = MagicMock(return_value=str(uuid4()))
    credentials = CamundaCloudCredentials(client_id, client_secret, cluster_id)
    zeebe_adapter = ZeebeAdapterBase(credentials=credentials)
    assert zeebe_adapter.connection_uri == f"{cluster_id}.bru-2.zeebe.camunda.io:443"


def test_credentials_no_connection_uri(zeebe_adapter):
    hostname = str(uuid4())
    port = randint(0, RANDOM_RANGE)
    url = f"https://{str(uuid4())}/oauth/token"
    client_id = str(uuid4())
    client_secret = str(uuid4())
    audience = str(uuid4())

    with patch("requests_oauthlib.OAuth2Session.post"):
        credentials = OAuthCredentials(url, client_id, client_secret, audience)
    zeebe_adapter = ZeebeAdapterBase(hostname=hostname, port=port, credentials=credentials)
    assert zeebe_adapter.connection_uri == f"{hostname}:{port}"


def test_common_zeebe_grpc_error_internal(zeebe_adapter):
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)
    with pytest.raises(ZeebeInternalError):
        zeebe_adapter._common_zeebe_grpc_errors(error)


def test_common_zeebe_grpc_error_back_pressure(zeebe_adapter):
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.RESOURCE_EXHAUSTED)
    with pytest.raises(ZeebeBackPressure):
        zeebe_adapter._common_zeebe_grpc_errors(error)


def test_common_zeebe_grpc_error_gateway_unavailable(zeebe_adapter):
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.UNAVAILABLE)
    with pytest.raises(ZeebeGatewayUnavailable):
        zeebe_adapter._common_zeebe_grpc_errors(error)


def test_common_zeebe_grpc_error_unkown_error(zeebe_adapter):
    error = grpc.RpcError()
    error._state = GRPCStatusCode("Nothing")
    with pytest.raises(grpc.RpcError):
        zeebe_adapter._common_zeebe_grpc_errors(error)


def test_close_after_retried_unavailable(zeebe_adapter):
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.UNAVAILABLE)
    zeebe_adapter._close = MagicMock()
    zeebe_adapter._max_connection_retries = 1
    with pytest.raises(ZeebeGatewayUnavailable):
        zeebe_adapter._common_zeebe_grpc_errors(error)

    zeebe_adapter._close.assert_called_once()


def test_close_after_retried_internal(zeebe_adapter):
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)
    zeebe_adapter._close = MagicMock()
    zeebe_adapter._max_connection_retries = 1
    with pytest.raises(ZeebeInternalError):
        zeebe_adapter._common_zeebe_grpc_errors(error)

    zeebe_adapter._close.assert_called_once()
