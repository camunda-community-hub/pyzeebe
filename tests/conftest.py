from random import randint
from threading import Event
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient, ZeebeWorker, Job
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.task import task_builder
from pyzeebe.task.task_config import TaskConfig
from pyzeebe.worker.task_router import ZeebeTaskRouter
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.random_utils import random_job


@pytest.fixture
def job_with_adapter(zeebe_adapter):
    return random_job(zeebe_adapter=zeebe_adapter)


@pytest.fixture
def mocked_job_with_adapter(job_with_adapter):
    job_with_adapter.set_success_status = MagicMock()
    job_with_adapter.set_failure_status = MagicMock()
    job_with_adapter.set_error_status = MagicMock()
    return job_with_adapter


@pytest.fixture
def job_without_adapter():
    return random_job()


@pytest.fixture
def job_from_task(task):
    job = random_job(task)
    job.variables = dict(x=str(uuid4()))
    return job


@pytest.fixture
def zeebe_adapter(grpc_create_channel):
    return ZeebeAdapter(channel=grpc_create_channel())


@pytest.fixture
def zeebe_client(grpc_create_channel):
    return ZeebeClient(channel=grpc_create_channel())


@pytest.fixture
def zeebe_worker(zeebe_adapter):
    worker = ZeebeWorker()
    worker.zeebe_adapter = zeebe_adapter
    return worker


@pytest.fixture
def task(original_task_function, task_config):
    return task_builder.build_task(original_task_function, task_config)


@pytest.fixture
def first_active_job(task, job_from_task, grpc_servicer) -> str:
    grpc_servicer.active_jobs[job_from_task.key] = job_from_task
    return job_from_task


@pytest.fixture
def task_config(task_type):
    return TaskConfig(
        type=task_type,
        exception_handler=MagicMock(),
        timeout_ms=10000,
        max_jobs_to_activate=32,
        variables_to_fetch=[],
        single_value=False,
        variable_name="",
        before=[],
        after=[]
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
    def simple_decorator(job: Job) -> Job:
        return job

    return MagicMock(wraps=simple_decorator)


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
