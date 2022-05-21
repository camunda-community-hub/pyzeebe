from asyncio import sleep
from typing import Dict
from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient
from pyzeebe.errors import ProcessDefinitionNotFoundError
from tests.integration.utils import ProcessStats


@pytest.mark.asyncio
async def test_run_process(
    zeebe_client: ZeebeClient, process_name: str, process_variables: Dict, process_stats: ProcessStats
):
    initial_amount_of_processes = process_stats.get_process_runs()

    await zeebe_client.run_process(process_name, process_variables)
    await sleep(0.2)  # Wait for process to finish

    assert process_stats.get_process_runs() == initial_amount_of_processes + 1


@pytest.mark.asyncio
async def test_non_existent_process(zeebe_client: ZeebeClient):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process(str(uuid4()))


@pytest.mark.asyncio
async def test_run_process_with_result(zeebe_client: ZeebeClient, process_name: str, process_variables: Dict):
    process_instance_key, process_result = await zeebe_client.run_process_with_result(process_name, process_variables)

    assert process_result["output"].startswith(process_variables["input"])


@pytest.mark.asyncio
async def test_cancel_process(zeebe_client: ZeebeClient, process_name: str, process_variables: Dict):
    process_key = await zeebe_client.run_process(process_name, process_variables)
    await zeebe_client.cancel_process_instance(process_key)
