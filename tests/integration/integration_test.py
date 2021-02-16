import os
from typing import Dict
from uuid import uuid4

import pytest

from pyzeebe import ZeebeWorker, ZeebeClient, Job
from pyzeebe.exceptions import WorkflowNotFound

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
        zeebe_client.deploy_workflow(os.path.join(integration_tests_path, "test.bpmn"))
    except FileNotFoundError:
        zeebe_client.deploy_workflow("test.bpmn")

    yield zeebe_client
    zeebe_worker.stop(wait=True)
    assert not zeebe_worker._watcher_thread.is_alive()


def test_run_workflow():
    workflow_key = zeebe_client.run_workflow("test", {"input": str(uuid4()), "should_throw": False})
    assert isinstance(workflow_key, int)


def test_non_existent_workflow():
    with pytest.raises(WorkflowNotFound):
        zeebe_client.run_workflow(str(uuid4()))


def test_run_workflow_with_result():
    input = str(uuid4())
    output = zeebe_client.run_workflow_with_result("test", {"input": input, "should_throw": False})
    assert isinstance(output["output"], str)
    assert output["output"].startswith(input)


def test_cancel_workflow():
    workflow_key = zeebe_client.run_workflow("test", {"input": str(uuid4()), "should_throw": False})
    zeebe_client.cancel_workflow_instance(workflow_key)
