import uuid

import pytest

from pyz.exceptions import TaskNotFoundException
from pyz.task.task import Task
from pyz.worker.worker import ZeebeWorker


@pytest.fixture(scope='module')
def grpc_add_to_server():
    from pyz.grpc_internals.zeebe_pb2_grpc import add_GatewayServicer_to_server
    return add_GatewayServicer_to_server()


@pytest.fixture(scope='module')
def grpc_servicer():
    from pyz.grpc_internals.zeebe_pb2_grpc import GatewayServicer
    return GatewayServicer()


@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
    from pyz.grpc_internals.zeebe_pb2_grpc import GatewayStub
    return GatewayStub


def test_add_before():
    base_decorator = ZeebeWorker()
    base_decorator.before(lambda x: x)
    assert len(base_decorator._before) == 1


def test_add_after():
    base_decorator = ZeebeWorker()
    base_decorator.after(lambda x: x)
    assert len(base_decorator._after) == 1


def test_add_before_plus_constructor():
    constructor_decorator = lambda x: x + 1
    function_decorator = lambda x: x

    base_decorator = ZeebeWorker(before=[constructor_decorator])
    base_decorator.before(function_decorator)
    assert len(base_decorator._before) == 2
    assert base_decorator._before == [constructor_decorator, function_decorator]


def test_add_after_plus_constructor():
    constructor_decorator = lambda x: x + 1
    function_decorator = lambda x: x

    base_decorator = ZeebeWorker(after=[constructor_decorator])
    base_decorator.after(function_decorator)
    assert len(base_decorator._after) == 2
    assert base_decorator._after == [constructor_decorator, function_decorator]


class TestZeebeWorker:
    def setup_class(self):
        self.zeebe_worker = ZeebeWorker()

    def _add_zeebe_task(self) -> str:
        task_type = str(uuid.uuid4())
        self.zeebe_worker.add_task(Task(task_type, lambda x: x, lambda x: x))
        return task_type

    def test_add_task(self):
        task_type = self._add_zeebe_task()
        assert self.zeebe_worker.get_task(task_type) is not None

    def test_remove_task(self):
        task_type = self._add_zeebe_task()
        assert self.zeebe_worker.remove_task(task_type) is not None
        with pytest.raises(TaskNotFoundException):
            self.zeebe_worker.get_task(task_type)

    def test_add_decorator(self):
        self.zeebe_worker = ZeebeWorker(before=[lambda x: x])
        assert len(self.zeebe_worker._before) == 1
