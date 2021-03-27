import os
from typing import Dict
from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient, ZeebeWorker, Job
from pyzeebe.errors import WorkflowNotFoundError


@pytest.fixture(scope="session")
def zeebe_client():
    return ZeebeClient()


@pytest.fixture(scope="session")
def zeebe_worker():
    worker = ZeebeWorker()

    def exception_handler(exc: Exception, job: Job) -> None:
        job.set_error_status(f"Failed to run task {job.type}. Reason: {exc}")

    @worker.task("test", exception_handler)
    def task_handler(should_throw: bool, input: str) -> Dict:
        if should_throw:
            raise Exception("Error thrown")
        else:
            return {"output": input + str(uuid4())}

    return worker


@pytest.fixture(scope="module", autouse=True)
def setup(zeebe_worker, zeebe_client):
    zeebe_worker.work(watch=True)

    try:
        integration_tests_path = os.path.join("tests", "integration")
        zeebe_client.deploy_workflow(
            os.path.join(integration_tests_path, "test.bpmn")
        )
    except FileNotFoundError:
        zeebe_client.deploy_workflow("test.bpmn")

    yield
    zeebe_worker.stop(wait=True)
    assert not zeebe_worker._watcher_thread.is_alive()


def test_run_workflow(zeebe_client: ZeebeClient):
    workflow_key = zeebe_client.run_workflow(
        "test",
        {"input": str(uuid4()), "should_throw": False}
    )
    assert isinstance(workflow_key, int)


def test_non_existent_workflow(zeebe_client: ZeebeClient):
    with pytest.raises(WorkflowNotFoundError):
        zeebe_client.run_workflow(str(uuid4()))


def test_run_workflow_with_result(zeebe_client: ZeebeClient):
    input = str(uuid4())
    workflow_instance_key, workflow_result = zeebe_client.run_workflow_with_result(
        "test",
        {"input": input, "should_throw": False}
    )
    assert isinstance(workflow_instance_key, int)
    assert isinstance(workflow_result["output"], str)
    assert workflow_result["output"].startswith(input)


def test_cancel_workflow(zeebe_client: ZeebeClient):
    workflow_key = zeebe_client.run_workflow(
        "test",
        {"input": str(uuid4()), "should_throw": False}
    )
    zeebe_client.cancel_workflow_instance(workflow_key)
