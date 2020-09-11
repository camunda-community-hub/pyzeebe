from random import randint
from threading import Event
from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.common.exceptions import TaskNotFound
from pyzeebe.common.gateway_mock import GatewayMock
from pyzeebe.common.random_utils import random_task_context
from pyzeebe.task.task import Task
from pyzeebe.task.task_context import TaskContext
from pyzeebe.worker.worker import ZeebeWorker

zeebe_worker: ZeebeWorker
task: Task


def decorator(context: TaskContext) -> TaskContext:
    return context


@pytest.fixture(scope='module')
def grpc_add_to_server():
    from pyzeebe.grpc_internals.zeebe_pb2_grpc import add_GatewayServicer_to_server
    return add_GatewayServicer_to_server


@pytest.fixture(scope='module')
def grpc_servicer():
    return GatewayMock()


@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
    from pyzeebe.grpc_internals.zeebe_pb2_grpc import GatewayStub
    return GatewayStub


@pytest.fixture(autouse=True)
def run_around_tests():
    global zeebe_worker, task
    task = Task(str(uuid4()), lambda x: {"x": x}, lambda x, y, z: x)
    zeebe_worker = ZeebeWorker()
    yield
    zeebe_worker = ZeebeWorker()
    task = Task(str(uuid4()), lambda x: {"x": x}, lambda x, y, z: x)


def test_add_task():
    zeebe_worker.add_task(task)
    assert len(zeebe_worker.tasks) == 1
    assert zeebe_worker.get_task(task.type).handler is not None

    variable = str(uuid4())
    assert task.inner_function(variable) == {'x': variable}

    assert callable(task.handler)
    context = random_task_context(task)
    context.variables = {'x': str(uuid4())}
    with patch('pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job') as mock:
        assert isinstance(task.handler(context), TaskContext)
        mock.assert_called_with(job_key=context.key, variables=context.variables)


def test_before_task_decorator_called():
    with patch('pyzeebe.worker.worker_test.decorator') as mock:
        context = random_task_context(task)
        context.variables = {'x': str(uuid4())}

        mock.return_value = context

        task.before(decorator)
        zeebe_worker.add_task(task)
        with patch('pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job') as grpc_mock:
            assert isinstance(task.handler(context), TaskContext)
            grpc_mock.assert_called_with(job_key=context.key, variables=context.variables)
        mock.assert_called_with(context)


def test_after_task_decorator_called():
    with patch('pyzeebe.worker.worker_test.decorator') as mock:
        context = random_task_context(task)
        context.variables = {'x': str(uuid4())}

        mock.return_value = context

        task.after(decorator)
        zeebe_worker.add_task(task)

        with patch('pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job') as grpc_mock:
            assert isinstance(task.handler(context), TaskContext)
            grpc_mock.assert_called_with(job_key=context.key, variables=context.variables)
        mock.assert_called_with(context)


def test_task_exception_handler_called():
    def task_handler(x):
        raise Exception()

    def exception_handler(e, context, status_setter):
        pass

    context = random_task_context(task)
    context.variables = {'x': str(uuid4())}

    task.inner_function = task_handler
    task.exception_handler = exception_handler

    with patch('pyzeebe.worker.worker_test.task.exception_handler') as mock:
        zeebe_worker.add_task(task)
        task.handler(context)
        mock.assert_called()


def test_remove_task():
    zeebe_worker.add_task(task)
    assert zeebe_worker.remove_task(task.type) is not None
    assert task not in zeebe_worker.tasks


def test_remove_task_from_many():
    zeebe_worker.add_task(task)

    for i in range(0, randint(0, 100)):
        zeebe_worker.add_task(Task(str(uuid4()), lambda x: x, lambda x: x))
    assert zeebe_worker.remove_task(task.type) is not None
    assert task not in zeebe_worker.tasks


def test_remove_fake_task():
    with pytest.raises(TaskNotFound):
        zeebe_worker.remove_task(str(uuid4()))


def test_get_fake_task():
    with pytest.raises(TaskNotFound):
        zeebe_worker.get_task(str(uuid4()))


def test_get_task():
    zeebe_worker.add_task(task)
    found_task = zeebe_worker.get_task(task.type)
    assert isinstance(found_task, Task)
    assert found_task == task


def test_get_task_index():
    zeebe_worker.add_task(task)
    index = zeebe_worker._get_task_index(task.type)
    assert isinstance(index, int)
    assert zeebe_worker.tasks[index] == task


def test_get_task_and_index():
    zeebe_worker.add_task(task)
    found_task, index = zeebe_worker._get_task_and_index(task.type)
    assert isinstance(index, int)
    assert zeebe_worker.tasks[index] == task
    assert isinstance(found_task, Task)
    assert found_task == task


def test_add_before_decorator():
    zeebe_worker.before(decorator)
    assert len(zeebe_worker._before) == 1
    assert decorator in zeebe_worker._before


def test_add_after_decorator():
    zeebe_worker.after(decorator)
    assert len(zeebe_worker._after) == 1
    assert decorator in zeebe_worker._after


def test_add_constructor_before_decorator():
    zeebe_worker = ZeebeWorker(before=[decorator])
    assert len(zeebe_worker._before) == 1
    assert decorator in zeebe_worker._before


def test_add_constructor_after_decorator():
    zeebe_worker = ZeebeWorker(after=[decorator])
    assert len(zeebe_worker._after) == 1
    assert decorator in zeebe_worker._after


def test_create_before_decorator_runner():
    task.before(decorator)
    context = random_task_context(task)
    context.variables = {'x': str(uuid4())}
    decorators = zeebe_worker._create_before_decorator_runner(task)
    assert isinstance(decorators(context), TaskContext)


def test_handle_one_job():
    context = random_task_context(task)

    with patch('pyzeebe.worker.worker.ZeebeWorker._get_task_contexts') as get_jobs_mock:
        get_jobs_mock.return_value = [context]
        with patch('pyzeebe.worker.worker_test.task.handler') as task_handler_mock:
            task_handler_mock.return_value = {'x': str(uuid4())}
            zeebe_worker._handle_task_contexts(task)
            task_handler_mock.assert_called_with(context)


def test_handle_no_job():
    context = random_task_context(task)

    with patch('pyzeebe.worker.worker.ZeebeWorker._get_task_contexts') as get_jobs_mock:
        get_jobs_mock.return_value = []
        with patch('pyzeebe.worker.worker_test.task.handler') as task_handler_mock:
            task_handler_mock.return_value = {'x': str(uuid4())}
            zeebe_worker._handle_task_contexts(task)
            with pytest.raises(AssertionError):
                task_handler_mock.assert_called_with(context)


def test_handle_many_jobs():
    context = random_task_context(task)

    with patch('pyzeebe.worker.worker.ZeebeWorker._get_task_contexts') as get_jobs_mock:
        get_jobs_mock.return_value = [context]
        with patch('pyzeebe.worker.worker_test.task.handler') as task_handler_mock:
            task_handler_mock.return_value = {'x': str(uuid4())}
            zeebe_worker._handle_task_contexts(task)
            task_handler_mock.assert_called_with(context)


def test_stop_worker():
    stop_event = Event()
    zeebe_worker.work(stop_event=stop_event)
    stop_event.set()
