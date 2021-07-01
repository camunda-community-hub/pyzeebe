from copy import deepcopy

import pytest

import pyzeebe.grpc
from pyzeebe.grpc import get_channel_options


@pytest.fixture
def revert_monkeypatch_after_test():
    """ This sort of exists in pytest already (docs.pytest.org/en/stable/monkeypatch.html),
    however that means a bit of "magic" happens, this is a bit clearer and tests the users
    approach to this."""
    options_before = deepcopy(pyzeebe.grpc.GRPC_CHANNEL_OPTIONS)
    yield
    pyzeebe.grpc.GRPC_CHANNEL_OPTIONS = options_before


def test_get_channel_options_returns_tuple_of_tuple_with_options():
    assert get_channel_options() == (
        ("grpc.keepalive_time_ms", 45000),
    )


@pytest.mark.usefixtures("revert_monkeypatch_after_test")
def test_monkeypatching_with_options_override():
    pyzeebe.grpc.GRPC_CHANNEL_OPTIONS["grpc.keepalive_time_ms"] = 4000
    assert get_channel_options() == (
        ("grpc.keepalive_time_ms", 4000),
    )


@pytest.mark.usefixtures("revert_monkeypatch_after_test")
def test_monkeypatching_with_options_added():
    pyzeebe.grpc.GRPC_CHANNEL_OPTIONS.update({
        "grpc.keepalive_timeout_ms": 120000,
        "grpc.http2.min_time_between_pings_ms": 60000,
    })
    assert get_channel_options() == (
        ("grpc.keepalive_time_ms", 45000),
        ("grpc.keepalive_timeout_ms", 120000),
        ("grpc.http2.min_time_between_pings_ms", 60000)
    )


@pytest.mark.usefixtures("revert_monkeypatch_after_test")
def test_monkeypatching_with_options_removed():
    pyzeebe.grpc.GRPC_CHANNEL_OPTIONS = {}
    assert get_channel_options() == ()
