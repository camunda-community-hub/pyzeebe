import os
from typing import Optional

DEFAULT_HOSTNAME = "localhost"
DEFAULT_PORT = 26500
DEFAULT_ADDRESS = f"{DEFAULT_HOSTNAME}:{DEFAULT_PORT}"


def create_address(
    hostname: Optional[str] = None,
    port: Optional[int] = None,
) -> str:
    if hostname or port:
        return f"{hostname or DEFAULT_HOSTNAME}:{port or DEFAULT_PORT}"
    return os.getenv("ZEEBE_ADDRESS", DEFAULT_ADDRESS)
