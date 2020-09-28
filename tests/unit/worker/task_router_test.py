from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.task_router import ZeebeTaskRouter

zeebe_task_router: ZeebeTaskRouter


def decorator(job: Job) -> Job:
    return job


@pytest.fixture(autouse=True)
def run_around_tests():
    global zeebe_task_router
    zeebe_task_router = ZeebeTaskRouter()
    yield
    zeebe_task_router = ZeebeTaskRouter()


def test_router_before_decorator():
    task_type = str(uuid4())
    zeebe_task_router.before(decorator)

    @zeebe_task_router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    task = zeebe_task_router.get_task(task_type)
    assert task is not None
    assert len(task._before) == 1
    assert len(task._after) == 0


def test_router_after_before_multiple():
    task_type = str(uuid4())
    zeebe_task_router.before(decorator)

    @zeebe_task_router.task(task_type=task_type, before=[decorator])
    def task_fn(x):
        return {"x": x}

    task = zeebe_task_router.get_task(task_type)
    assert task is not None
    assert len(task._before) == 2
    assert len(task._after) == 0


def test_router_after_decorator():
    task_type = str(uuid4())
    zeebe_task_router.after(decorator)

    @zeebe_task_router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    task = zeebe_task_router.get_task(task_type)
    assert task is not None
    assert len(task._after) == 1
    assert len(task._before) == 0


def test_router_after_decorator_multiple():
    task_type = str(uuid4())
    zeebe_task_router.after(decorator)

    @zeebe_task_router.task(task_type=task_type, after=[decorator])
    def task_fn(x):
        return {"x": x}

    task = zeebe_task_router.get_task(task_type)
    assert task is not None
    assert len(task._after) == 2
    assert len(task._before) == 0


def test_router_non_dict_task():
    with patch("pyzeebe.worker.task_handler.ZeebeTaskHandler._single_value_function_to_dict") as single_value_mock:
        task_type = str(uuid4())
        variable_name = str(uuid4())

        @zeebe_task_router.task(task_type=task_type, single_value=True, variable_name=variable_name)
        def task_fn(x):
            return {"x": x}

        single_value_mock.assert_called_with(variable_name=variable_name, fn=task_fn)
    assert len(zeebe_task_router.tasks) == 1


def test_router_dict_task():
    task_type = str(uuid4())

    @zeebe_task_router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    assert len(zeebe_task_router.tasks) == 1


def test_add_decorators_to_task():
    task = Task(task_handler=lambda x: x, exception_handler=lambda x: x, task_type=str(uuid4()))
    zeebe_task_router._add_decorators_to_task(task, [decorator], [decorator])
    assert len(task._before) == 1
    assert len(task._after) == 1


def test_add_decorators_to_task_with_router_decorators():
    task = Task(task_handler=lambda x: x, exception_handler=lambda x: x, task_type=str(uuid4()))
    zeebe_task_router.before(decorator)
    zeebe_task_router.after(decorator)
    zeebe_task_router._add_decorators_to_task(task, [decorator], [decorator])
    assert len(task._before) == 2
    assert len(task._after) == 2
