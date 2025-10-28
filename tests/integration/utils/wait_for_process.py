from anyio import sleep

from .process_stats import ProcessStats


async def wait_for_process(process_instance_key: int, process_stats: ProcessStats, interval: float = 0.2):
    while not process_stats.has_process_been_run(process_instance_key):
        await sleep(interval)


async def wait_for_process_with_variables(process_stats: ProcessStats, variables: dict, interval: float = 0.2):
    while not process_stats.has_process_with_variables_been_run(variables):
        await sleep(interval)
