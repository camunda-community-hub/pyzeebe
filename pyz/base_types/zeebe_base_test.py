from unittest.mock import patch

import grpc
import pytest

from pyz.base_types.zeebe_base import ZeebeBase


@patch('grpc.insecure_channel')
def mock():
    pass


zeebe_base = ZeebeBase()


@pytest.fixture(autouse=True)
def run_around_tests():
    global zeebe_base
    zeebe_base = ZeebeBase()
    yield
    zeebe_base = ZeebeBase


def test_connectivity_ready():
    zeebe_base._check_connectivity(grpc.ChannelConnectivity.READY)
    assert not zeebe_base.retrying_connection
    assert zeebe_base.connected


def test_connectivity_transient_idle():
    zeebe_base._check_connectivity(grpc.ChannelConnectivity.IDLE)
    assert not zeebe_base.retrying_connection
    assert zeebe_base.connected


def test_connectivity_connecting():
    zeebe_base._check_connectivity(grpc.ChannelConnectivity.CONNECTING)
    assert zeebe_base.retrying_connection
    assert not zeebe_base.connected


def test_connectivity_transient_failure():
    zeebe_base._check_connectivity(grpc.ChannelConnectivity.TRANSIENT_FAILURE)
    assert zeebe_base.retrying_connection
    assert not zeebe_base.connected


def test_connectivity_shutdown():
    with pytest.raises(ConnectionAbortedError):
        zeebe_base._check_connectivity(grpc.ChannelConnectivity.SHUTDOWN)
