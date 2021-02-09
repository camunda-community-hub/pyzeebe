from random import randint
from uuid import uuid4

import pytest

from pyzeebe import ZeebeClient, ZeebeWorker, ZeebeTaskRouter
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
def task():
    return Task(str(uuid4()), lambda x: {"x": x}, lambda x, y, z: x)


@pytest.fixture
def router():
    return ZeebeTaskRouter()


@pytest.fixture
def routers():
    return [ZeebeTaskRouter() for _ in range(0, randint(2, 100))]


@pytest.fixture
def task_handler():
    return ZeebeTaskHandler()


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
