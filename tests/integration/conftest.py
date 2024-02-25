import asyncio
import os
from typing import Dict
from uuid import uuid4

import grpc
import pytest

from pyzeebe import Job, ZeebeClient, ZeebeWorker, create_insecure_channel
from tests.integration.utils import ProcessRun, ProcessStats


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def grpc_channel():
    return create_insecure_channel()


@pytest.fixture(scope="module")
def zeebe_client(grpc_channel: grpc.aio.Channel):
    return ZeebeClient(grpc_channel)


@pytest.fixture(scope="module")
def zeebe_worker(grpc_channel):
    return ZeebeWorker(grpc_channel)


@pytest.fixture(autouse=True, scope="module")
def task(zeebe_worker: ZeebeWorker, process_stats: ProcessStats):
    async def exception_handler(exc: Exception, job: Job) -> None:
        await job.set_error_status(f"Failed to run task {job.type}. Reason: {exc}")

    @zeebe_worker.task("test", exception_handler)
    async def task_handler(should_throw: bool, input: str, job: Job) -> Dict:
        process_stats.add_process_run(ProcessRun(job.process_instance_key, job.variables))
        if should_throw:
            raise Exception("Error thrown")
        else:
            return {"output": input + str(uuid4())}


@pytest.fixture(autouse=True, scope="module")
async def deploy_process(zeebe_client: ZeebeClient):
    try:
        integration_tests_path = os.path.join("tests", "integration")
        await zeebe_client.deploy_process(os.path.join(integration_tests_path, "test.bpmn"))
    except FileNotFoundError:
        await zeebe_client.deploy_process("test.bpmn")


@pytest.fixture(autouse=True, scope="module")
def start_worker(event_loop: asyncio.AbstractEventLoop, zeebe_worker: ZeebeWorker):
    event_loop.create_task(zeebe_worker.work())
    yield
    event_loop.create_task(zeebe_worker.stop())


@pytest.fixture(scope="module")
def process_name() -> str:
    return "test"


@pytest.fixture
def process_variables() -> Dict:
    return {"input": str(uuid4()), "should_throw": False}


@pytest.fixture(scope="module")
def process_stats(process_name: str) -> ProcessStats:
    return ProcessStats(process_name)
