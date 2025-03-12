import pytest

from pyzeebe.grpc_internals.types import HealthCheckResponse, TopologyResponse
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter


@pytest.mark.asyncio
class TestTopology:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeAdapter):
        response = await zeebe_adapter.topology()

        assert isinstance(response, TopologyResponse)


@pytest.mark.xfail(reason="Required GRPC health checking stubs")
@pytest.mark.asyncio
class TestHealthCheck:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeAdapter):
        response = await zeebe_adapter.healthcheck()

        assert isinstance(response, HealthCheckResponse)
