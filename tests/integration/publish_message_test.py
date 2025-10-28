import pytest

from pyzeebe import ZeebeClient
from tests.integration.utils import ProcessStats
from tests.integration.utils.wait_for_process import wait_for_process_with_variables

pytestmark = [pytest.mark.e2e, pytest.mark.anyio]


async def test_publish_message(zeebe_client: ZeebeClient, process_stats: ProcessStats, process_variables: dict):
    initial_amount_of_processes = process_stats.get_process_runs()

    await zeebe_client.publish_message("start_test_process", correlation_key="", variables=process_variables)
    await wait_for_process_with_variables(process_stats, process_variables)

    assert process_stats.get_process_runs() == initial_amount_of_processes + 1
