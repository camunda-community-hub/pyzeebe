import asyncio
import os
from typing import Dict
from uuid import uuid4

import grpc
import pytest

from pyzeebe import Job, ZeebeClient, ZeebeWorker, create_insecure_channel
from pyzeebe.errors import ProcessDefinitionNotFoundError


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
def task(zeebe_worker: ZeebeWorker):
    def exception_handler(exc: Exception, job: Job) -> None:
        job.set_error_status(f"Failed to run task {job.type}. Reason: {exc}")

    @zeebe_worker.task("test", exception_handler)
    async def task_handler(should_throw: bool, input: str) -> Dict:
        if should_throw:
            raise Exception("Error thrown")
        else:
            return {"output": input + str(uuid4())}


@pytest.mark.asyncio
@pytest.fixture(autouse=True, scope="module")
async def deploy_process(zeebe_client: ZeebeClient):
    try:
        integration_tests_path = os.path.join("tests", "integration")
        await zeebe_client.deploy_process(
            os.path.join(integration_tests_path, "test.bpmn")
        )
    except FileNotFoundError:
        await zeebe_client.deploy_process("test.bpmn")


@pytest.fixture(autouse=True, scope="module")
def start_worker(event_loop: asyncio.AbstractEventLoop, zeebe_worker: ZeebeWorker):
    event_loop.create_task(zeebe_worker.work())
    yield
    event_loop.create_task(zeebe_worker.stop())


@pytest.mark.asyncio
async def test_run_process(zeebe_client: ZeebeClient):
    process_key = await zeebe_client.run_process(
        "test", {"input": str(uuid4()), "should_throw": False}
    )
    assert isinstance(process_key, int)


@pytest.mark.asyncio
async def test_non_existent_process(zeebe_client: ZeebeClient):
    with pytest.raises(ProcessDefinitionNotFoundError):
        await zeebe_client.run_process(str(uuid4()))


@pytest.mark.asyncio
async def test_run_process_with_result(zeebe_client: ZeebeClient):
    input = str(uuid4())
    process_instance_key, process_result = await zeebe_client.run_process_with_result(
        "test", {"input": input, "should_throw": False}
    )
    assert isinstance(process_instance_key, int)
    assert isinstance(process_result["output"], str)
    assert process_result["output"].startswith(input)


@pytest.mark.asyncio
async def test_cancel_process(zeebe_client: ZeebeClient):
    process_key = await zeebe_client.run_process(
        "test", {"input": str(uuid4()), "should_throw": False}
    )
    await zeebe_client.cancel_process_instance(process_key)
