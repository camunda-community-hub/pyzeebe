""" gRPC Channel Options

``grpc.keepalive_time_ms``
--------------------------

Time between keepalive pings. Following the official Zeebe Java/Go client, sending pings every 45 seconds.

https://docs.camunda.io/docs/product-manuals/zeebe/deployment-guide/operations/setting-up-a-cluster/#keep-alive-intervals
"""
from typing import Any, Dict, Tuple

GRPC_CHANNEL_OPTIONS = {
    "grpc.keepalive_time_ms": 45_000
}


def get_channel_options(options: Dict[str, Any] = None) -> Tuple[Tuple[str, Any], ...]:
    """
    Convert options dict to tuple in expected format for creating the gRPC channel

    Args:
        options (Dict[str, Any]): A key/value representation of `gRPC channel arguments_`.
            Default: None (will use library defaults)

    Returns:
        Tuple[Tuple[str, Any], ...]: Options for the gRPC channel

    .. _gRPC channel arguments:
        https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments
    """
    if options:
        options = {**GRPC_CHANNEL_OPTIONS, **options}
    else:
        options = GRPC_CHANNEL_OPTIONS
    return tuple(
        (k, v) for k, v in options.items()
    )
