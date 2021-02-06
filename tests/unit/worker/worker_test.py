from random import randint
from unittest.mock import patch, MagicMock
from uuid import uuid4
import time

import pytest

from pyzeebe.exceptions import DuplicateTaskType, MaxConsecutiveTaskThreadError
from pyzeebe.job.job import Job
from pyzeebe.worker.worker import ZeebeWorker
from tests.unit.utils.random_utils import random_job


def test_add_task_saves_task(zeebe_worker, task):
    zeebe_worker._add_task(task)

    assert zeebe_worker.get_task(task.type) == task


def test_add_duplicate_task(zeebe_worker, task):
    zeebe_worker._add_task(task)
    with pytest.raises(DuplicateTaskType):
        zeebe_worker._add_task(task)


def test_only_one_task_added(zeebe_worker):
    @zeebe_worker.task(str(uuid4()))
    def _():
        pass

    assert len(zeebe_worker.tasks) == 1


def test_task_type_saved(zeebe_worker, task):
    zeebe_worker._add_task(task)

    assert zeebe_worker.get_task(task.type).type == task.type


def test_original_function_not_changed(zeebe_worker, task):
    zeebe_worker._add_task(task)
    job = random_job(task)
    job.variables = {"x": str(uuid4())}

    assert task.inner_function(**job.variables) == job.variables


def test_task_handler_calls_original_function(zeebe_worker, task):
    job = random_job(task)
    job.variables = {"x": str(uuid4())}

    zeebe_worker._add_task(task)
    task.handler(job)

    task.inner_function.assert_called_once()


def test_task_timeout_saved(zeebe_worker, task):
    timeout = randint(0, 10000)
    task.timeout = timeout

    zeebe_worker._add_task(task)

    assert zeebe_worker.get_task(task.type).timeout == timeout


def test_task_max_jobs_saved(zeebe_worker, task):
    max_jobs_to_activate = randint(0, 1000)
    task.max_jobs_to_activate = max_jobs_to_activate

    zeebe_worker._add_task(task)

    assert zeebe_worker.get_task(task.type).max_jobs_to_activate == max_jobs_to_activate


def test_task_variables_to_fetch_are_correct(zeebe_worker, task_type):
    expected_variables_to_fetch = ["x"]

    @zeebe_worker.task(task_type)
    def _(x):
        pass

    assert zeebe_worker.get_task(task_type).variables_to_fetch == expected_variables_to_fetch


def test_task_handler_is_callable(zeebe_worker, task):
    zeebe_worker._add_task(task)

    assert callable(task.handler)


def test_before_task_decorator_called(zeebe_worker, task, decorator):
    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}

    task.before(decorator)
    zeebe_worker._add_task(task)

    task.handler(job)

    decorator.assert_called_with(job)


def test_after_task_decorator_called(zeebe_worker, task, decorator):
    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}

    task.after(decorator)
    zeebe_worker._add_task(task)

    task.handler(job)

    decorator.assert_called_with(job)


def test_decorator_failed(zeebe_worker, task, decorator):
    job = random_job(task=task)

    decorator.side_effect = Exception()
    zeebe_worker.before(decorator)
    zeebe_worker.after(decorator)
    zeebe_worker._add_task(task)

    assert isinstance(task.handler(job), Job)
    assert decorator.call_count == 2


def test_task_exception_handler_called(zeebe_worker, task):
    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}
    task.inner_function.side_effect = Exception()
    task.exception_handler = MagicMock()
    zeebe_worker._add_task(task)

    task.handler(job)

    task.exception_handler.assert_called()


def test_add_before_decorator(zeebe_worker, decorator):
    zeebe_worker.before(decorator)
    assert len(zeebe_worker._before) == 1
    assert decorator in zeebe_worker._before


def test_add_after_decorator(zeebe_worker, decorator):
    zeebe_worker.after(decorator)
    assert len(zeebe_worker._after) == 1
    assert decorator in zeebe_worker._after


def test_add_constructor_before_decorator(decorator):
    zeebe_worker = ZeebeWorker(before=[decorator])
    assert len(zeebe_worker._before) == 1
    assert decorator in zeebe_worker._before


def test_add_constructor_after_decorator(decorator):
    zeebe_worker = ZeebeWorker(after=[decorator])
    assert len(zeebe_worker._after) == 1
    assert decorator in zeebe_worker._after


def test_create_before_decorator_runner(zeebe_worker, task, decorator):
    task.before(decorator)
    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}
    decorators = zeebe_worker._create_before_decorator_runner(task)
    assert isinstance(decorators(job), Job)


def test_handle_one_job(zeebe_worker, task):
    job = random_job(task=task)

    with patch("pyzeebe.worker.worker.ZeebeWorker._get_jobs") as get_jobs_mock:
        get_jobs_mock.return_value = [job]
        task.handler = MagicMock(return_value={"x": str(uuid4())})
        zeebe_worker._handle_jobs(task)
        task.handler.assert_called_with(job)


def test_handle_no_job(zeebe_worker, task):
    job = random_job(task=task)

    zeebe_worker._get_jobs = MagicMock(return_value=[])
    task.handler = MagicMock(return_value={"x": str(uuid4())})
    zeebe_worker._handle_jobs(task)

    with pytest.raises(AssertionError):
        task.handler.assert_called_with(job)


def test_handle_many_jobs(zeebe_worker, task):
    job = random_job(task=task)

    with patch("pyzeebe.worker.worker.ZeebeWorker._get_jobs") as get_jobs_mock:
        get_jobs_mock.return_value = [job]
        task.handler = MagicMock(return_value={"x": str(uuid4())})
        zeebe_worker._handle_jobs(task)
        task.handler.assert_called_with(job)


def test_work_thread_start_called(zeebe_worker, task):
    with patch("pyzeebe.worker.worker.Thread") as thread_mock:
        thread_instance_mock = MagicMock()
        thread_mock.return_value = thread_instance_mock
        zeebe_worker._add_task(task)
        zeebe_worker.work()
        zeebe_worker.stop()
        thread_instance_mock.start.assert_called_once()


def test_stop_worker(zeebe_worker):
    zeebe_worker.work()
    zeebe_worker.stop()


def test_include_router(zeebe_worker, router, task_type):
    @router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    zeebe_worker.include_router(router)
    assert zeebe_worker.get_task(task_type) is not None


def test_include_multiple_routers(zeebe_worker, routers, task_type):
    for router in routers:
        @router.task(str(uuid4()))
        def task_fn(x):
            return {"x": x}

        zeebe_worker.include_router(router)

    assert len(zeebe_worker.tasks) == len(routers)


def test_router_before_decorator(zeebe_worker, router, decorator, task_type):
    router.before(decorator)

    @router.task(task_type=task_type, before=[decorator])
    def task_fn(x):
        return {"x": x}

    zeebe_worker.before(decorator)
    zeebe_worker.include_router(router)

    task = zeebe_worker.get_task(task_type)

    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}

    decorator.return_value = job

    with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as grpc_mock:
        assert isinstance(task.handler(job), Job)
        grpc_mock.assert_called_with(job_key=job.key, variables=job.variables)

    assert decorator.call_count == 3


def test_router_after_decorator(zeebe_worker, router, decorator, task_type):
    router.after(decorator)

    @router.task(task_type=task_type, after=[decorator])
    def task_fn(x):
        return {"x": x}

    zeebe_worker.after(decorator)
    zeebe_worker.include_router(router)

    task = zeebe_worker.get_task(task_type)

    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}

    decorator.return_value = job

    with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as grpc_mock:
        assert isinstance(task.handler(job), Job)
        grpc_mock.assert_called_with(job_key=job.key, variables=job.variables)

    assert decorator.call_count == 3


def test_router_non_dict_task(zeebe_worker, task_type):
    with patch("pyzeebe.worker.task_handler.ZeebeTaskHandler._single_value_function_to_dict") as single_value_mock:
        variable_name = str(uuid4())

        @zeebe_worker.task(task_type=task_type, single_value=True, variable_name=variable_name)
        def task_fn(x):
            return {"x": x}

        single_value_mock.assert_called_with(variable_name=variable_name, fn=task_fn)
    assert len(zeebe_worker.tasks) == 1


def test_get_jobs(zeebe_worker, task):
    zeebe_worker.zeebe_adapter.activate_jobs = MagicMock()
    zeebe_worker._get_jobs(task)
    zeebe_worker.zeebe_adapter.activate_jobs.assert_called_with(task_type=task.type, worker=zeebe_worker.name,
                                                                timeout=task.timeout,
                                                                max_jobs_to_activate=task.max_jobs_to_activate,
                                                                variables_to_fetch=task.variables_to_fetch,
                                                                request_timeout=zeebe_worker.request_timeout)


def test_watch_task_threads_dont_restart_running_threads(
        zeebe_worker, task, handle_task_mock, stop_event_mock, handle_not_alive_thread_spy, stop_after_test):
    def fake_task_handler_never_return(*_args):
        while not stop_after_test.is_set():
            time.sleep(0.05)

    handle_task_mock.side_effect = fake_task_handler_never_return
    zeebe_worker._add_task(task)
    zeebe_worker.watcher_max_errors_factor = 2
    # change stop_event.is_set on nth call
    stop_event_mock.is_set.side_effect = [False, False, True, True]
    zeebe_worker.work(watch=False)
    zeebe_worker._watch_task_threads(frequency=0)

    assert handle_not_alive_thread_spy.call_count == 0

def test_watch_task_threads_that_die_get_restarted_then_exit_after_too_many_errors(
        zeebe_worker, task, handle_task_mock, stop_event_mock, handle_not_alive_thread_spy):
    def fake_task_handler_return_immediately(*_args):
        pass

    handle_task_mock.side_effect = fake_task_handler_return_immediately
    zeebe_worker._add_task(task)
    zeebe_worker.watcher_max_errors_factor = 2
    # change stop_event.is_set on nth call
    stop_event_mock.is_set.return_value = False
    zeebe_worker.work(watch=False)
    with pytest.raises(MaxConsecutiveTaskThreadError) as exc_info:
        zeebe_worker._watch_task_threads(frequency=0)

    assert "consecutive errors (2)" in exc_info.value.args[0]
    assert handle_not_alive_thread_spy.call_count == 1
