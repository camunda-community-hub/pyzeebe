import asyncio

import pytest


@pytest.fixture
def queue() -> asyncio.Queue:
    return asyncio.Queue()
