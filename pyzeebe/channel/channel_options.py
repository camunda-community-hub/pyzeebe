""" gRPC Channel Options

``grpc.keepalive_time_ms``
--------------------------

Time between keepalive pings. Following the official Zeebe Java/Go client, sending pings every 45 seconds.

https://docs.camunda.io/docs/product-manuals/zeebe/deployment-guide/operations/setting-up-a-cluster/#keep-alive-intervals
"""

from __future__ import annotations

from pyzeebe.types import ChannelArgumentType

GRPC_CHANNEL_OPTIONS_DEFAULT: ChannelArgumentType = (("grpc.keepalive_time_ms", 45_000),)


def get_channel_options(options: ChannelArgumentType | None = None) -> ChannelArgumentType:
    """
    Get default channel options for creating the gRPC channel.

    Args:
        options (Optional[ChannelArgumentType]): A tuple of gRPC channel arguments tuple.
            e.g. (("grpc.keepalive_time_ms", 45_000),)
            Default: None (will use library defaults)
            See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

    Returns:
        ChannelArgumentType: Options for the gRPC channel
    """
    if options is not None:
        existing = set()
        _options = []

        for a, b in (*options, *GRPC_CHANNEL_OPTIONS_DEFAULT):
            if a not in existing:  # NOTE: Remove duplicates, fist one wins
                existing.add(a)
                _options.append((a, b))

        return tuple(_options)  # (*options, GRPC_CHANNEL_OPTIONS)
    return GRPC_CHANNEL_OPTIONS_DEFAULT
