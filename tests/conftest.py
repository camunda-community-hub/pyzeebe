from random import randint
from threading import Event
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient, ZeebeWorker, ZeebeTaskRouter, Job
from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.task.task import Task
from pyzeebe.worker.task_handler import ZeebeTaskHandler
from tests.unit.utils.gateway_mock import GatewayMock
from tests.unit.utils.random_utils import random_job


@pytest.fixture
def job_with_adapter(zeebe_adapter):
    return random_job(zeebe_adapter=zeebe_adapter)


@pytest.fixture
def job_without_adapter():
    return random_job()


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
def task(task_type):
    return Task(task_type, MagicMock(wraps=lambda x: {"x": x}), MagicMock(wraps=lambda x, y, z: x))


@pytest.fixture
def task_type():
    return str(uuid4())


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
def task_handler():
    return ZeebeTaskHandler()


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
