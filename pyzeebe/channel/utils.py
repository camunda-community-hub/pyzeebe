import os
from typing import Optional

DEFAULT_HOSTNAME = "localhost"
DEFAULT_PORT = 26500
DEFAULT_ADDRESS = f"{DEFAULT_HOSTNAME}:{DEFAULT_PORT}"


def create_address(
    grpc_address: Optional[str] = None,
) -> str:
    if grpc_address:
        return grpc_address
    return os.getenv("ZEEBE_ADDRESS", DEFAULT_ADDRESS)
