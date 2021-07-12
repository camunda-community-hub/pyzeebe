import os
from typing import Optional


def create_address(
    hostname: Optional[str] = None,
    port: Optional[int] = None,
) -> str:
    if hostname or port:
        return f"{hostname or 'localhost'}:{port or 26500}"
    return os.getenv("ZEEBE_ADDRESS", "localhost:26500")
