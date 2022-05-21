from typing import Dict

import pytest

from pyzeebe import ZeebeClient


@pytest.mark.asyncio
async def test_cancel_process(zeebe_client: ZeebeClient, process_name: str, process_variables: Dict):
    process_key = await zeebe_client.run_process(process_name, process_variables)

    await zeebe_client.cancel_process_instance(process_key)
