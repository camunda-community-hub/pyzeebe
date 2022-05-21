from asyncio import sleep
from typing import Dict

import pytest

from pyzeebe import ZeebeClient
from tests.integration.utils.process_stats import ProcessStats


@pytest.mark.asyncio
async def test_publish_message(zeebe_client: ZeebeClient, process_stats: ProcessStats, process_variables: Dict):
    initial_amount_of_processes = process_stats.get_process_runs()

    await zeebe_client.publish_message("start_test_process", correlation_key="", variables=process_variables)

    await sleep(0.2)  # Wait for process to finish

    assert process_stats.get_process_runs() == initial_amount_of_processes + 1
