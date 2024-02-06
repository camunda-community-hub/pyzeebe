from typing import Dict
from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient
from pyzeebe.errors import ProcessDefinitionNotFoundError
from tests.integration.utils import ProcessStats, wait_for_process

PROCESS_TIMEOUT_IN_MS = 60_000


async def test_run_process(
    zeebe_client: ZeebeClient, process_name: str, process_variables: Dict, process_stats: ProcessStats
):
    initial_amount_of_processes = process_stats.get_process_runs()

    process_instance_key = await zeebe_client.run_process(process_name, process_variables)
    await wait_for_process(process_instance_key, process_stats)

    assert process_stats.get_process_runs() == initial_amount_of_processes + 1


async def test_non_existent_process(zeebe_client: ZeebeClient):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process(str(uuid4()))


async def test_run_process_with_result(zeebe_client: ZeebeClient, process_name: str, process_variables: Dict):
    _, process_result = await zeebe_client.run_process_with_result(
        process_name, process_variables, timeout=PROCESS_TIMEOUT_IN_MS
    )

    assert process_result["output"].startswith(process_variables["input"])
