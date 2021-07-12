from typing import Dict, Optional

import grpc

from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import create_address


def create_insecure_channel(
    hostname: Optional[str] = None,
    port: Optional[int] = None,
    channel_options: Optional[Dict] = None
) -> grpc.aio.Channel:
    """
    Create an insecure channel

    Args:
        hostname (Optional[str], optional): Zeebe gateway hostname
        port (Optional[int], optional): Zeebe gateway port
        channel_options (Optional[Dict], optional): GRPC channel options. See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

    Returns:
        grpc.aio.Channel: A GRPC Channel connected to the Zeebe gateway.
    """
    address = create_address(hostname, port)
    return grpc.aio.insecure_channel(address, options=get_channel_options(channel_options))
