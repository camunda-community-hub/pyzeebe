import pytest

from pyzeebe import ZeebeClient
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.random_utils import random_job


@pytest.fixture
def job():
    return random_job()


@pytest.fixture
def zeebe_adapter(grpc_channel):
    return ZeebeAdapter(channel=grpc_channel)


@pytest.fixture
def zeebe_client(grpc_channel):
    return ZeebeClient(channel=grpc_channel)


@pytest.fixture(scope="module")
def grpc_add_to_server():
    from zeebe_grpc.gateway_pb2_grpc import add_GatewayServicer_to_server
    return add_GatewayServicer_to_server


@pytest.fixture(scope="module")
def grpc_servicer():
    return GatewayMock()


@pytest.fixture(scope="module")
def grpc_stub_cls(grpc_channel):
    from zeebe_grpc.gateway_pb2_grpc import GatewayStub
    return GatewayStub
