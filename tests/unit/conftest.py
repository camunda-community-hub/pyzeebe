from random import randint
from threading import Event
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import grpc
import pytest
import pytest_asyncio

from pyzeebe import Job, ZeebeClient, ZeebeWorker
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import JobController
from pyzeebe.task import task_builder
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.worker.task_router import ZeebeTaskRouter
from pyzeebe.worker.task_state import TaskState
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.random_utils import random_job


@pytest.fixture
def job_controller(job):
    return JobController(job=job, zeebe_adapter=AsyncMock())


@pytest.fixture
def mocked_job_controller(job):
    job_controller = JobController(job, MagicMock())
    job_controller.set_running_after_decorators_status = AsyncMock()
    job_controller.set_success_status = AsyncMock()
    job_controller.set_failure_status = AsyncMock()
    job_controller.set_error_status = AsyncMock()
    return job_controller


@pytest.fixture
def job():
    return random_job()


@pytest.fixture
def job_from_task(task):
    job = random_job(task, variables=dict(x=str(uuid4())))
    return job


@pytest.fixture
def zeebe_adapter(aio_grpc_channel: grpc.aio.Channel):
    adapter = ZeebeAdapter(aio_grpc_channel)
    return adapter


@pytest.fixture
def zeebe_client(aio_grpc_channel: grpc.aio.Channel):
    client = ZeebeClient(aio_grpc_channel)
    return client


@pytest.fixture
def zeebe_worker(aio_grpc_channel: grpc.aio.Channel):
    worker = ZeebeWorker(aio_grpc_channel)
    return worker


@pytest.fixture
def task(original_task_function, task_config):
    return task_builder.build_task(original_task_function, task_config)


@pytest.fixture
def first_active_job(task, job_from_task, grpc_servicer) -> str:
    grpc_servicer.active_jobs[job_from_task.key] = job_from_task
    return job_from_task


@pytest.fixture
def task_config(task_type, variables_to_fetch=None):
    return TaskConfig(
        type=task_type,
        exception_handler=AsyncMock(),
        timeout_ms=10000,
        max_jobs_to_activate=32,
        max_running_jobs=32,
        variables_to_fetch=variables_to_fetch or [],
        single_value=False,
        variable_name="",
        before=[],
        after=[],
    )


@pytest.fixture
def task_type():
    return str(uuid4())


@pytest.fixture
def original_task_function():
    def original_function():
        pass

    mock = MagicMock(wraps=original_function)
    mock.__code__ = original_function.__code__
    return mock


@pytest.fixture
def stop_after_test():
    stop_test = Event()
    yield stop_test
    stop_test.set()


@pytest.fixture
def handle_task_mock():
    with patch("pyzeebe.worker.worker.ZeebeWorker._handle_task") as mock:
        yield mock


@pytest.fixture
def stop_event_mock(zeebe_worker):
    with patch.object(zeebe_worker, "stop_event") as mock:
        yield mock


@pytest.fixture
def handle_not_alive_thread_spy(mocker):
    spy = mocker.spy(ZeebeWorker, "_handle_not_alive_thread")
    yield spy


@pytest.fixture
def router():
    return ZeebeTaskRouter()


@pytest.fixture
def routers():
    return [ZeebeTaskRouter() for _ in range(0, randint(2, 100))]


@pytest.fixture
def decorator():
    async def simple_decorator(job: Job) -> Job:
        return job

    return AsyncMock(wraps=simple_decorator)


@pytest.fixture
def exception_handler():
    async def simple_exception_handler(e: Exception, job: Job, job_controller: JobController) -> None:
        return None

    return AsyncMock(wraps=simple_exception_handler)


@pytest.fixture(scope="module")
def grpc_add_to_server():
    from zeebe_grpc.gateway_pb2_grpc import add_GatewayServicer_to_server

    return add_GatewayServicer_to_server


@pytest.fixture(scope="module")
def grpc_servicer():
    return GatewayMock()


@pytest.fixture(scope="module")
def grpc_stub_cls(grpc_channel):
    from zeebe_grpc.gateway_pb2_grpc import GatewayStub

    return GatewayStub


@pytest.fixture
def aio_create_grpc_channel(request, grpc_addr, grpc_server):
    return grpc.aio.insecure_channel(grpc_addr)


@pytest_asyncio.fixture
async def aio_grpc_channel(aio_create_grpc_channel):
    async with aio_create_grpc_channel as channel:
        yield channel


@pytest.fixture
def task_state() -> TaskState:
    return TaskState()
