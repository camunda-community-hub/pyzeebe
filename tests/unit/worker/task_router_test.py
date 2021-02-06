from random import randint
from unittest.mock import patch
from uuid import uuid4

from pyzeebe.job.job import Job


def decorator(job: Job) -> Job:
    return job


def test_add_task_through_decorator(router):
    task_type = str(uuid4())
    timeout = randint(0, 10000)
    max_jobs_to_activate = randint(0, 1000)

    @router.task(task_type=task_type, timeout=timeout, max_jobs_to_activate=max_jobs_to_activate)
    def example_test_task(x):
        return {"x": x}

    assert len(router.tasks) == 1

    variable = str(uuid4())
    assert example_test_task(variable) == {"x": variable}

    task = router.get_task(task_type)
    assert task is not None

    variable = str(uuid4())
    assert task.inner_function(variable) == {"x": variable}
    assert task.variables_to_fetch == ["x"]
    assert task.timeout == timeout
    assert task.max_jobs_to_activate == max_jobs_to_activate


def test_router_before_decorator(router):
    task_type = str(uuid4())
    router.before(decorator)

    @router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    task = router.get_task(task_type)
    assert task is not None
    assert len(task._before) == 1
    assert len(task._after) == 0


def test_router_after_before_multiple(router):
    task_type = str(uuid4())
    router.before(decorator)

    @router.task(task_type=task_type, before=[decorator])
    def task_fn(x):
        return {"x": x}

    task = router.get_task(task_type)
    assert task is not None
    assert len(task._before) == 2
    assert len(task._after) == 0


def test_router_after_decorator(router):
    task_type = str(uuid4())
    router.after(decorator)

    @router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    task = router.get_task(task_type)
    assert task is not None
    assert len(task._after) == 1
    assert len(task._before) == 0


def test_router_after_decorator_multiple(router):
    task_type = str(uuid4())
    router.after(decorator)

    @router.task(task_type=task_type, after=[decorator])
    def task_fn(x):
        return {"x": x}

    task = router.get_task(task_type)
    assert task is not None
    assert len(task._after) == 2
    assert len(task._before) == 0


def test_router_non_dict_task(router):
    with patch("pyzeebe.worker.task_handler.ZeebeTaskHandler._single_value_function_to_dict") as single_value_mock:
        task_type = str(uuid4())
        variable_name = str(uuid4())

        @router.task(task_type=task_type, single_value=True, variable_name=variable_name)
        def task_fn(x):
            return {"x": x}

        single_value_mock.assert_called_with(variable_name=variable_name, fn=task_fn)
    assert len(router.tasks) == 1


def test_router_dict_task(router):
    task_type = str(uuid4())

    @router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    assert len(router.tasks) == 1


def test_add_decorators_to_task(router, task):
    router._add_decorators_to_task(task, [decorator], [decorator])
    assert len(task._before) == 1
    assert len(task._after) == 1


def test_add_decorators_to_task_with_router_decorators(router, task):
    router.before(decorator)
    router.after(decorator)
    router._add_decorators_to_task(task, [decorator], [decorator])
    assert len(task._before) == 2
    assert len(task._after) == 2
