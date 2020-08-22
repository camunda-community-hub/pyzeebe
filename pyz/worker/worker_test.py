from random import randint
from unittest.mock import patch
from uuid import uuid4

import pytest

from pyz.common.test_utils import random_job_context
from pyz.exceptions import TaskNotFoundException
from pyz.task.job_context import JobContext
from pyz.task.task import Task
from pyz.worker.worker import ZeebeWorker

zeebe_worker: ZeebeWorker
task: Task


def decorator(context: JobContext) -> JobContext:
    return context


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
    context = random_job_context(task)
    context.variables = {'x': str(uuid4())}
    with patch('pyz.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job') as mock:
        assert isinstance(task.handler(context), dict)
    # TODO: Assert completeJob called


def test_before_task_decorator_called():
    with patch('pyz.worker.worker_test.decorator') as mock:
        context = random_job_context(task)
        context.variables = {'x': str(uuid4())}

        mock.return_value = context

        task.before(decorator)
        zeebe_worker.add_task(task)
        with patch('pyz.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job') as grpc_mock:
            assert isinstance(task.handler(context), dict)
        mock.assert_called_with(context)


def test_after_task_decorator_called():
    with patch('pyz.worker.worker_test.decorator') as mock:
        context = random_job_context(task)
        context.variables = {'x': str(uuid4())}

        mock.return_value = context

        task.after(decorator)
        zeebe_worker.add_task(task)

        with patch('pyz.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job') as grpc_mock:
            assert isinstance(task.handler(context), dict)
        mock.assert_called_with(context)


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
    with pytest.raises(TaskNotFoundException):
        zeebe_worker.remove_task(str(uuid4()))


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
    context = random_job_context(task)
    context.variables = {'x': str(uuid4())}
    decorators = zeebe_worker._create_before_decorator_runner(task)
    assert isinstance(decorators(context), JobContext)


def test_handle_one_job():
    context = random_job_context(task)

    with patch('pyz.worker.worker.ZeebeWorker._get_jobs') as get_jobs_mock:
        get_jobs_mock.return_value = [context]
        with patch('pyz.worker.worker_test.task.handler') as task_handler_mock:
            task_handler_mock.return_value = {'x': str(uuid4())}
            zeebe_worker.handle_task_jobs(task)
            task_handler_mock.assert_called_with(context)


def test_handle_no_job():
    context = random_job_context(task)

    with patch('pyz.worker.worker.ZeebeWorker._get_jobs') as get_jobs_mock:
        get_jobs_mock.return_value = []
        with patch('pyz.worker.worker_test.task.handler') as task_handler_mock:
            task_handler_mock.return_value = {'x': str(uuid4())}
            zeebe_worker.handle_task_jobs(task)
            with pytest.raises(AssertionError):
                task_handler_mock.assert_called_with(context)


def test_handle_many_jobs():
    context = random_job_context(task)

    with patch('pyz.worker.worker.ZeebeWorker._get_jobs') as get_jobs_mock:
        get_jobs_mock.return_value = [context]
        with patch('pyz.worker.worker_test.task.handler') as task_handler_mock:
            task_handler_mock.return_value = {'x': str(uuid4())}
            zeebe_worker.handle_task_jobs(task)
            task_handler_mock.assert_called_with(context)
