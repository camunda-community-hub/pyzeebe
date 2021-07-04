import os
from typing import Any, Dict, Optional

import grpc

from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.grpc_internals.channel_options import get_channel_options


def create_connection_uri(
    hostname: str = None,
    port: int = None,
    credentials: BaseCredentials = None
) -> str:
    if credentials and credentials.get_connection_uri():
        return credentials.get_connection_uri()
    if hostname or port:
        return f"{hostname or 'localhost'}:{port or 26500}"
    return os.getenv("ZEEBE_ADDRESS", "localhost:26500")


def create_channel(
    connection_uri: str,
    credentials: Optional[BaseCredentials] = None,
    secure_connection: bool = False,
    options: Dict[str, Any] = None
) -> grpc.aio.Channel:
    """
    options: A key/value representation of `gRPC channel arguments_`. Default: None (will use library defaults)

    .. _gRPC channel arguments:
        https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments
    """
    channel_options = get_channel_options(options)
    if credentials:
        return grpc.aio.secure_channel(connection_uri, credentials.grpc_credentials, options=channel_options)
    if secure_connection:
        return grpc.aio.secure_channel(connection_uri, grpc.ssl_channel_credentials(), options=channel_options)
    return grpc.aio.insecure_channel(connection_uri, options=channel_options)
