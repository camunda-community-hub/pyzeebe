import pytest

from pyzeebe import ZeebeClient

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_ping(zeebe_client: ZeebeClient):
    healthcheck = await zeebe_client.healthcheck()

    assert healthcheck.status == healthcheck.ServingStatus.SERVING
