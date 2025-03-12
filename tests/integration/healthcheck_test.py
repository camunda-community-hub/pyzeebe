import pytest

from pyzeebe import ZeebeClient


@pytest.mark.e2e
async def test_ping(zeebe_client: ZeebeClient):
    healthcheck = await zeebe_client.healthcheck()

    assert healthcheck.status == healthcheck.ServingStatus.SERVING
