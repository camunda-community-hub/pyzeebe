from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient
from pyzeebe.errors import ProcessDefinitionNotFoundError
from tests.integration.utils import ProcessStats, wait_for_process

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]

PROCESS_TIMEOUT_IN_MS = 60_000


async def test_run_process(
    zeebe_client: ZeebeClient, process_name: str, process_variables: dict, process_stats: ProcessStats
):
    initial_amount_of_processes = process_stats.get_process_runs()

    process_instance_key = await zeebe_client.run_process(process_name, process_variables)
    await wait_for_process(process_instance_key.process_instance_key, process_stats)

    assert process_stats.get_process_runs() == initial_amount_of_processes + 1


async def test_non_existent_process(zeebe_client: ZeebeClient):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process(str(uuid4()))


async def test_run_process_with_result(zeebe_client: ZeebeClient, process_name: str, process_variables: dict):
    response = await zeebe_client.run_process_with_result(
        process_name, process_variables, timeout=PROCESS_TIMEOUT_IN_MS
    )

    assert response.variables["output"].startswith(process_variables["input"])
