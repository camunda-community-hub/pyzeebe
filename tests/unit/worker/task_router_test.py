from uuid import uuid4

import pytest

from pyzeebe import TaskDecorator
from pyzeebe.exceptions import TaskNotFoundError, DuplicateTaskType
from pyzeebe.task.task import Task
from pyzeebe.worker.task_router import ZeebeTaskRouter
from tests.unit.utils.random_utils import randint


def test_get_task(router: ZeebeTaskRouter, task: Task):
    router.tasks.append(task)

    found_task = router.get_task(task.type)

    assert found_task == task


def test_get_fake_task(router: ZeebeTaskRouter):
    with pytest.raises(TaskNotFoundError):
        router.get_task(str(uuid4()))


def test_get_task_index(router: ZeebeTaskRouter, task: Task):
    router.tasks.append(task)

    index = router._get_task_index(task.type)

    assert router.tasks[index] == task


def test_get_task_and_index(router: ZeebeTaskRouter, task: Task):
    router.tasks.append(task)

    found_task, index = router._get_task_and_index(task.type)

    assert router.tasks[index] == task
    assert found_task == task


def test_remove_task(router: ZeebeTaskRouter, task: Task):
    router.tasks.append(task)

    router.remove_task(task.type)

    assert task not in router.tasks


def test_remove_task_from_many(router: ZeebeTaskRouter, task: Task):
    router.tasks.append(task)

    for _ in range(1, randint(0, 100)):
        @router.task(str(uuid4()))
        def dummy_function():
            pass

    router.remove_task(task.type)

    assert task not in router.tasks


def test_remove_fake_task(router: ZeebeTaskRouter):
    with pytest.raises(TaskNotFoundError):
        router.remove_task(str(uuid4()))


def test_check_is_task_duplicate_with_duplicate(router: ZeebeTaskRouter, task: Task):
    router.tasks.append(task)
    with pytest.raises(DuplicateTaskType):
        router._is_task_duplicate(task.type)


def test_check_is_task_duplicate_no_duplicate(router: ZeebeTaskRouter, task: Task):
    router.tasks.append(task)


def test_add_before_decorator(router: ZeebeTaskRouter, decorator: TaskDecorator):
    router.before(decorator)

    assert len(router._before) == 1


def test_add_after_decorator(router: ZeebeTaskRouter, decorator: TaskDecorator):
    router.after(decorator)

    assert len(router._after) == 1


def test_add_before_decorator_through_constructor(decorator: TaskDecorator):
    router = ZeebeTaskRouter(before=[decorator])

    assert len(router._before) == 1


def test_add_after_decorator_through_constructor(decorator: TaskDecorator):
    router = ZeebeTaskRouter(after=[decorator])

    assert len(router._after) == 1
