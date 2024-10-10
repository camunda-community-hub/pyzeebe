from __future__ import annotations

import os

DEFAULT_ZEEBE_ADDRESS = "localhost:26500"


def create_address(
    grpc_address: str | None = None,
) -> str:
    if grpc_address:
        return grpc_address
    return os.getenv("ZEEBE_ADDRESS", DEFAULT_ZEEBE_ADDRESS)
