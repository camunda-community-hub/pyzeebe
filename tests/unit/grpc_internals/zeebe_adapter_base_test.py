from random import randint
from unittest.mock import patch, MagicMock
from uuid import uuid4

from pyzeebe.credentials.camunda_cloud_credentials import CamundaCloudCredentials
from pyzeebe.credentials.oauth_credentials import OAuthCredentials
from pyzeebe.exceptions import ZeebeBackPressure, ZeebeGatewayUnavailable, ZeebeInternalError
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from tests.unit.utils.grpc_utils import *
from tests.unit.utils.random_utils import RANDOM_RANGE

zeebe_adapter: ZeebeAdapterBase


@pytest.fixture(autouse=True)
def run_around_tests(grpc_channel):
    global zeebe_adapter
    zeebe_adapter = ZeebeAdapterBase(channel=grpc_channel)
    yield
    zeebe_adapter = ZeebeAdapterBase(channel=grpc_channel)


def test_connectivity_ready():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.READY)
    assert not zeebe_adapter.retrying_connection
    assert zeebe_adapter.connected


def test_connectivity_transient_idle():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.IDLE)
    assert not zeebe_adapter.retrying_connection
    assert zeebe_adapter.connected


def test_connectivity_connecting():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.CONNECTING)
    assert zeebe_adapter.retrying_connection
    assert not zeebe_adapter.connected


def test_connectivity_transient_failure():
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.TRANSIENT_FAILURE)
    assert zeebe_adapter.retrying_connection
    assert not zeebe_adapter.connected


def test_connectivity_transient_failure_logs_warning(caplog):
    zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.TRANSIENT_FAILURE)
    expected_logger = "pyzeebe.grpc_internals.zeebe_adapter_base"
    expected_level = "WARNING"
    matching_logs = [
        log
        for log in caplog.records
        if log.name == expected_logger and log.levelname == expected_level
    ]
    assert len(matching_logs) > 0


def test_connectivity_shutdown():
    with pytest.raises(ConnectionAbortedError):
        zeebe_adapter._check_connectivity(grpc.ChannelConnectivity.SHUTDOWN)


def test_only_port():
    port = randint(0, 10000)
    zeebe_adapter = ZeebeAdapterBase(port=port)
    assert zeebe_adapter.connection_uri == f"localhost:{port}"


def test_only_host():
    hostname = str(uuid4())
    zeebe_adapter = ZeebeAdapterBase(hostname=hostname)
    assert zeebe_adapter.connection_uri == f"{hostname}:26500"


def test_host_and_port():
    hostname = str(uuid4())
    port = randint(0, 10000)
    zeebe_adapter = ZeebeAdapterBase(hostname=hostname, port=port)
    assert zeebe_adapter.connection_uri == f"{hostname}:{port}"


def test_with_secure_connection():
    with patch("grpc.secure_channel") as grpc_secure_channel_mock:
        ZeebeAdapterBase(secure_connection=True)
        grpc_secure_channel_mock.assert_called()


def test_with_camunda_cloud_credentials():
    CamundaCloudCredentials.get_access_token = MagicMock()
    CamundaCloudCredentials.get_access_token.return_value = str(uuid4())
    credentials = CamundaCloudCredentials(str(uuid4()), str(uuid4()), str(uuid4()))

    with patch("grpc.secure_channel") as grpc_secure_channel_mock:
        ZeebeAdapterBase(credentials=credentials)
        grpc_secure_channel_mock.assert_called()


def test_credentials_connection_uri_gotten():
    client_id = str(uuid4())
    client_secret = str(uuid4())
    cluster_id = str(uuid4())
    CamundaCloudCredentials.get_access_token = MagicMock()
    CamundaCloudCredentials.get_access_token.return_value = str(uuid4())
    credentials = CamundaCloudCredentials(client_id, client_secret, cluster_id)
    zeebe_adapter = ZeebeAdapterBase(credentials=credentials)
    assert zeebe_adapter.connection_uri == f"{cluster_id}.zeebe.camunda.io:443"


def test_credentials_no_connection_uri():
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


def test_common_zeebe_grpc_error_internal():
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.INTERNAL)
    with pytest.raises(ZeebeInternalError):
        zeebe_adapter._common_zeebe_grpc_errors(error)


def test_common_zeebe_grpc_error_back_pressure():
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.RESOURCE_EXHAUSTED)
    with pytest.raises(ZeebeBackPressure):
        zeebe_adapter._common_zeebe_grpc_errors(error)


def test_common_zeebe_grpc_error_gateway_unavailable():
    error = grpc.RpcError()
    error._state = GRPCStatusCode(grpc.StatusCode.UNAVAILABLE)
    with pytest.raises(ZeebeGatewayUnavailable):
        zeebe_adapter._common_zeebe_grpc_errors(error)


def test_common_zeebe_grpc_error_unkown_error():
    error = grpc.RpcError()
    error._state = GRPCStatusCode("Nothing")
    with pytest.raises(grpc.RpcError):
        zeebe_adapter._common_zeebe_grpc_errors(error)
