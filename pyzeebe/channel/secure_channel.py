from typing import Dict, Optional

import grpc

from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import create_address


def create_secure_channel(
    hostname: Optional[str] = None,
    port: Optional[int] = None,
    channel_options: Optional[Dict] = None,
    channel_credentials: Optional[grpc.ChannelCredentials] = None,
) -> grpc.aio.Channel:
    """
    Create a secure channel

    Args:
        hostname (Optional[str], optional): Zeebe gateway hostname
        port (Optional[int], optional): Zeebe gateway port
        channel_options (Optional[Dict], optional): GRPC channel options. See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments
        channel_credentials (Optional[grpc.ChannelCredentials]): Channel credentials to use. Will use grpc.ssl_channel_credentials() if not provided.

    Returns:
        grpc.aio.Channel: A GRPC Channel connected to the Zeebe gateway.
    """
    address = create_address(hostname, port)
    credentials = channel_credentials or grpc.ssl_channel_credentials()
    return grpc.aio.secure_channel(
        address, credentials, options=get_channel_options(channel_options)
    )
