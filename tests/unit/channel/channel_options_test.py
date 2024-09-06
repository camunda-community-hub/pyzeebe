from pyzeebe.channel.channel_options import get_channel_options


def test_get_channel_options_returns_tuple_of_tuple_with_options():
    assert get_channel_options() == (("grpc.keepalive_time_ms", 45_000),)


def test_overrides_default_values_if_provided():
    grpc_options = (("grpc.keepalive_time_ms", 4_000),)

    assert get_channel_options(grpc_options) == (("grpc.keepalive_time_ms", 4_000),)


def test_adds_custom_options():
    grpc_options = (
        ("grpc.keepalive_timeout_ms", 120_000),
        ("grpc.http2.min_time_between_pings_ms", 60_000),
    )

    assert get_channel_options(grpc_options) == (
        ("grpc.keepalive_timeout_ms", 120_000),
        ("grpc.http2.min_time_between_pings_ms", 60_000),
        ("grpc.keepalive_time_ms", 45_000),
    )
