import os
from uuid import uuid4

import anyio
import grpc
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from pyzeebe import Job, ZeebeClient, ZeebeWorker, create_insecure_channel
from pyzeebe.job.job import JobController
from tests.integration.utils import ProcessRun, ProcessStats

ZEEBE_IMAGE_VERSION = os.getenv("ZEEBE_IMAGE_VERSION", "8.5.25")


@pytest.fixture(scope="package")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def zeebe_container():
    zeebe = (
        DockerContainer(f"camunda/zeebe:{ZEEBE_IMAGE_VERSION}")
        # envs for camunda 8.8+ due to https://github.com/camunda/camunda/issues/31904
        .with_envs(
            CAMUNDA_SECURITY_AUTHENTICATION_UNPROTECTEDAPI="true",
            CAMUNDA_SECURITY_AUTHORIZATIONS_ENABLED="false",
        )
        .with_exposed_ports(26500)
        .waiting_for(LogMessageWaitStrategy(r"Partition-1 recovered, marking it as healthy").with_startup_timeout(30))
    )

    with zeebe:
        yield zeebe


@pytest.fixture(scope="package")
async def grpc_channel(anyio_backend, zeebe_container: DockerContainer):
    return create_insecure_channel(
        grpc_address=f"{zeebe_container.get_container_host_ip()}:{zeebe_container.get_exposed_port(26500)}"
    )


@pytest.fixture(scope="package")
def zeebe_client(grpc_channel: grpc.aio.Channel):
    return ZeebeClient(grpc_channel)


@pytest.fixture(scope="package")
def zeebe_worker(grpc_channel):
    return ZeebeWorker(grpc_channel)


@pytest.fixture(scope="package")
def task(zeebe_worker: ZeebeWorker, process_stats: ProcessStats):
    async def exception_handler(exc: Exception, job: Job, job_controller: JobController) -> None:
        await job_controller.set_error_status(f"Failed to run task {job.type}. Reason: {exc}")

    @zeebe_worker.task("test", exception_handler)
    async def task_handler(should_throw: bool, input: str, job: Job) -> dict:
        process_stats.add_process_run(ProcessRun(job.process_instance_key, job.variables))
        if should_throw:
            raise Exception("Error thrown")
        else:
            return {"output": input + str(uuid4())}


@pytest.fixture(autouse=True, scope="package")
async def deploy_process(zeebe_client: ZeebeClient):
    try:
        integration_tests_path = os.path.join("tests", "integration")
        await zeebe_client.deploy_resource(os.path.join(integration_tests_path, "test.bpmn"))
    except FileNotFoundError:
        await zeebe_client.deploy_resource("test.bpmn")


@pytest.fixture(autouse=True, scope="package")
async def deploy_dmn(zeebe_client: ZeebeClient):
    try:
        integration_tests_path = os.path.join("tests", "integration")
        response = await zeebe_client.deploy_resource(os.path.join(integration_tests_path, "test.dmn"))
    except FileNotFoundError:
        response = await zeebe_client.deploy_resource("test.dmn")

    return response.deployments[0].decision_key


@pytest.fixture(autouse=True, scope="package")
async def start_worker(task, zeebe_worker: ZeebeWorker):
    async with anyio.create_task_group() as tg:
        tg.start_soon(zeebe_worker.work)
        yield
        tg.start_soon(zeebe_worker.stop)


@pytest.fixture(scope="package")
def process_name() -> str:
    return "test"


@pytest.fixture
def process_variables() -> dict:
    return {"input": str(uuid4()), "should_throw": False}


@pytest.fixture(scope="package")
def process_stats(process_name: str) -> ProcessStats:
    return ProcessStats(process_name)


@pytest.fixture(scope="package")
def decision_id() -> str:
    return "test"


@pytest.fixture(scope="package")
def decision_key(deploy_dmn) -> int:
    return deploy_dmn
