import grpc
import pytest

from tests.unit.utils.gateway_mock import GatewayMock


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


class GRPCStatusCode:
    def __init__(self, code: grpc.StatusCode):
        self.code = code
