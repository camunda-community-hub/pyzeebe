from copy import deepcopy

import pytest

import pyzeebe.channel.channel_options
from pyzeebe.channel.channel_options import get_channel_options


def test_get_channel_options_returns_tuple_of_tuple_with_options():
    assert get_channel_options() == (("grpc.keepalive_time_ms", 45000),)


def test_overrides_default_values_if_provided():
    grpc_options = {"grpc.keepalive_time_ms": 4000}

    assert get_channel_options(grpc_options) == (("grpc.keepalive_time_ms", 4000),)


def test_adds_custom_options():
    grpc_options = {
        "grpc.keepalive_timeout_ms": 120000,
        "grpc.http2.min_time_between_pings_ms": 60000,
    }

    assert get_channel_options(grpc_options) == (
        ("grpc.keepalive_time_ms", 45000),
        ("grpc.keepalive_timeout_ms", 120000),
        ("grpc.http2.min_time_between_pings_ms", 60000),
    )
