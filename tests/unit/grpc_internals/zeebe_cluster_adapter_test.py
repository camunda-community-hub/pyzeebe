import pytest

from pyzeebe import ZeebeGRPCAdapter as ZeebeAdapter
from pyzeebe.adapters.types import HealthCheckResponse, TopologyResponse


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
