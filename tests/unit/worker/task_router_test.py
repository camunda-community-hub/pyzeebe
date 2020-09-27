from uuid import uuid4

import pytest

from pyzeebe.job.job import Job
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
