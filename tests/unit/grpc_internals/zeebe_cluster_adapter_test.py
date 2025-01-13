import pytest

from pyzeebe.grpc_internals.types import TopologyResponse
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter


@pytest.mark.asyncio
class TestTopology:
    async def test_response_is_of_correct_type(self, zeebe_adapter: ZeebeAdapter):
        response = await zeebe_adapter.topology()

        assert isinstance(response, TopologyResponse)
