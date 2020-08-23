import pytest

from zeebepy.client.client import ZeebeClient

zeebe_client: ZeebeClient


@pytest.fixture(autouse=True)
def run_around_tests():
    global zeebe_client
    zeebe_client = ZeebeClient()
    yield
    zeebe_client = ZeebeClient()


def test_start_workflow():
    assert isinstance(zeebe_client.run_workflow(), str)


def test_start_workflow_with_result():
    assert isinstance(zeebe_client.run_workflow_with_result(), dict)
