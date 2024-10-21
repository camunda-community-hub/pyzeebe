from __future__ import annotations

import grpc

from pyzeebe.channel.channel_options import get_channel_options
from pyzeebe.channel.utils import get_zeebe_address
from pyzeebe.types import ChannelArgumentType


def create_insecure_channel(
    grpc_address: str | None = None, channel_options: ChannelArgumentType | None = None
) -> grpc.aio.Channel:
    """
    Create an insecure channel

    Args:
        grpc_address (Optional[str]): Zeebe Gateway Address
            Default: None, alias the ZEEBE_ADDRESS environment variable or "localhost:26500"
        channel_options (Optional[ChannelArgumentType]): GRPC channel options.
            See https://grpc.github.io/grpc/python/glossary.html#term-channel_arguments

    Returns:
        grpc.aio.Channel: A GRPC Channel connected to the Zeebe gateway.
    """
    grpc_address = grpc_address or get_zeebe_address()
    return grpc.aio.insecure_channel(target=grpc_address, options=get_channel_options(channel_options))
