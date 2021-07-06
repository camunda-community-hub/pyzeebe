from copy import deepcopy

import pytest
from unittest.mock import patch, Mock

from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase

import pyzeebe.grpc_internals.channel_options
from pyzeebe.grpc_internals.channel_options import get_channel_options


@pytest.fixture
def revert_monkeypatch_after_test():
    """
    This sort of exists in pytest already (docs.pytest.org/en/stable/monkeypatch.html),
    however that means a bit of "magic" happens, this is a bit clearer and tests the users
    approach to this.
    """
    options_before = deepcopy(pyzeebe.grpc_internals.channel_options.GRPC_CHANNEL_OPTIONS)
    yield
    pyzeebe.grpc_internals.channel_options.GRPC_CHANNEL_OPTIONS = options_before


def test_get_channel_options_returns_tuple_of_tuple_with_options():
    assert get_channel_options() == (
        ("grpc.keepalive_time_ms", 45000),
    )


@pytest.mark.parametrize("grpc_method,call_kwargs",
                         [
                             ("grpc.secure_channel", {"secure_connection": True}),
                             ("grpc.insecure_channel", {"secure_connection": False}),
                             ("grpc.secure_channel", {"credentials": Mock()}),
                         ])
def test_create_channel_called_with_options(grpc_method, call_kwargs, zeebe_adapter):
    with patch(grpc_method) as channel_mock:
        ZeebeAdapterBase(**call_kwargs)
        expected_options = (('grpc.keepalive_time_ms', 45000),)
        # `call_args.kwargs` as it's not available in python <=3.7
        # https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock.call_args
        # 0 is args, 1 is kwargs
        assert channel_mock.call_args[1]["options"] == expected_options


@pytest.mark.usefixtures("revert_monkeypatch_after_test")
def test_monkeypatching_with_options_override():
    pyzeebe.grpc_internals.channel_options.GRPC_CHANNEL_OPTIONS["grpc.keepalive_time_ms"] = 4000
    assert get_channel_options() == (
        ("grpc.keepalive_time_ms", 4000),
    )


@pytest.mark.usefixtures("revert_monkeypatch_after_test")
def test_monkeypatching_with_options_added():
    pyzeebe.grpc_internals.channel_options.GRPC_CHANNEL_OPTIONS.update({
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
    pyzeebe.grpc_internals.channel_options.GRPC_CHANNEL_OPTIONS = {}
    assert get_channel_options() == ()
