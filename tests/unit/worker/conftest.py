import asyncio

import pytest


@pytest.fixture
async def queue() -> asyncio.Queue:
    return asyncio.Queue()
