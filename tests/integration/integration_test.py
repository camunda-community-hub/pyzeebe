import os
from typing import Dict
from uuid import uuid4

import pytest

from pyzeebe import ZeebeWorker, ZeebeClient, Job
from pyzeebe.exceptions import ProcessNotFound

zeebe_client: ZeebeClient
zeebe_worker = ZeebeWorker()


def exception_handler(exc: Exception, job: Job) -> None:
    job.set_error_status(f"Failed to run task {job.type}. Reason: {exc}")


@zeebe_worker.task(task_type="test", exception_handler=exception_handler)
def task_handler(should_throw: bool, input: str) -> Dict:
    if should_throw:
        raise Exception("Error thrown")
    else:
        return {"output": input + str(uuid4())}


@pytest.fixture(scope="module", autouse=True)
def setup():
    global zeebe_client, task_handler

    zeebe_worker.work(watch=True)

    zeebe_client = ZeebeClient()
    try:
        integration_tests_path = os.path.join("tests", "integration")
        zeebe_client.deploy_process(
            os.path.join(integration_tests_path, "test.bpmn")
        )
    except FileNotFoundError:
        zeebe_client.deploy_process("test.bpmn")

    yield zeebe_client
    zeebe_worker.stop(wait=True)
    assert not zeebe_worker._watcher_thread.is_alive()


def test_run_process():
    process_key = zeebe_client.run_process(
        "test",
        {"input": str(uuid4()), "should_throw": False}
    )
    assert isinstance(process_key, int)


def test_non_existent_process():
    with pytest.raises(ProcessNotFound):
        zeebe_client.run_process(str(uuid4()))


def test_run_process_with_result():
    input = str(uuid4())
    process_instance_key, process_result = zeebe_client.run_process_with_result(
        "test",
        {"input": input, "should_throw": False}
    )
    assert isinstance(process_instance_key, int)
    assert isinstance(process_result["output"], str)
    assert process_result["output"].startswith(input)


def test_cancel_process():
    process_key = zeebe_client.run_process(
        "test",
        {"input": str(uuid4()), "should_throw": False}
    )
    zeebe_client.cancel_process_instance(process_key)
