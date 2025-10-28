import pytest

from pyzeebe import ZeebeClient

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_topology(zeebe_client: ZeebeClient):
    topology = await zeebe_client.topology()

    assert topology.cluster_size == 1
