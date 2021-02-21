from random import randint
from unittest.mock import patch, MagicMock
from uuid import uuid4
import time

import pytest

from pyzeebe.exceptions import DuplicateTaskType, MaxConsecutiveTaskThreadError
from pyzeebe.job.job import Job
from pyzeebe.worker.worker import ZeebeWorker


class TestAddTask:
    def test_task_added(self, zeebe_worker, task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type) == task

    def test_raises_on_duplicate(self, zeebe_worker, task):
        zeebe_worker._add_task(task)
        with pytest.raises(DuplicateTaskType):
            zeebe_worker._add_task(task)

    def test_only_one_task_added(self, zeebe_worker):
        @zeebe_worker.task(str(uuid4()))
        def _():
            pass

        assert len(zeebe_worker.tasks) == 1

    def test_task_type_saved(self, zeebe_worker, task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type).type == task.type

    def test_original_function_not_changed(self, zeebe_worker, task, job_from_task):
        zeebe_worker._add_task(task)

        assert task.inner_function(**job_from_task.variables) == job_from_task.variables

    def test_task_handler_calls_original_function(self, zeebe_worker, task, job_from_task):
        zeebe_worker._add_task(task)

        task.handler(job_from_task)

        task.inner_function.assert_called_once()

    def test_task_timeout_saved(self, zeebe_worker, task):
        timeout = randint(0, 10000)
        task.timeout = timeout

        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type).timeout == timeout

    def test_task_max_jobs_saved(self, zeebe_worker, task):
        max_jobs_to_activate = randint(0, 1000)
        task.max_jobs_to_activate = max_jobs_to_activate

        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type).max_jobs_to_activate == max_jobs_to_activate

    def test_variables_to_fetch_match_function_parameters(self, zeebe_worker, task_type):
        expected_variables_to_fetch = ["x"]

        @zeebe_worker.task(task_type)
        def _(x):
            pass

        assert zeebe_worker.get_task(task_type).variables_to_fetch == expected_variables_to_fetch

    def test_task_handler_is_callable(self, zeebe_worker, task):
        zeebe_worker._add_task(task)

        assert callable(task.handler)

    def test_exception_handler_called(self, zeebe_worker, task, job_from_task):
        task.inner_function.side_effect = Exception()
        task.exception_handler = MagicMock()
        zeebe_worker._add_task(task)

        task.handler(job_from_task)

        task.exception_handler.assert_called()


class TestDecorator:
    def test_add_before_decorator(self, zeebe_worker, decorator):
        zeebe_worker.before(decorator)
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    def test_add_after_decorator(self, zeebe_worker, decorator):
        zeebe_worker.after(decorator)
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after

    def test_add_constructor_before_decorator(self, decorator):
        zeebe_worker = ZeebeWorker(before=[decorator])
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    def test_add_constructor_after_decorator(self, decorator):
        zeebe_worker = ZeebeWorker(after=[decorator])
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after

    def test_create_before_decorator_runner(self, zeebe_worker, task, decorator, job_from_task):
        task.before(decorator)

        decorators = zeebe_worker._create_before_decorator_runner(task)

        assert isinstance(decorators(job_from_task), Job)

    def test_before_task_decorator_called(self, zeebe_worker, task, decorator, job_from_task):
        task.before(decorator)
        zeebe_worker._add_task(task)

        task.handler(job_from_task)

        decorator.assert_called_with(job_from_task)

    def test_after_task_decorator_called(self, zeebe_worker, task, decorator, job_from_task):
        task.after(decorator)
        zeebe_worker._add_task(task)

        task.handler(job_from_task)

        decorator.assert_called_with(job_from_task)

    def test_decorator_failed(self, zeebe_worker, task, decorator, job_from_task):
        decorator.side_effect = Exception()
        zeebe_worker.before(decorator)
        zeebe_worker.after(decorator)
        zeebe_worker._add_task(task)

        assert isinstance(task.handler(job_from_task), Job)
        assert decorator.call_count == 2


class TestHandleJobs:
    @pytest.fixture(autouse=True)
    def get_jobs_mock(self, zeebe_worker):
        zeebe_worker._get_jobs = MagicMock()
        return zeebe_worker._get_jobs

    @pytest.fixture(autouse=True)
    def task_handler_mock(self, task):
        task.handler = MagicMock(wraps=task.handler)

    def test_handle_no_job(self, zeebe_worker, task, get_jobs_mock):
        get_jobs_mock.return_value = []

        zeebe_worker._handle_jobs(task)

        task.handler.assert_not_called()

    def test_handle_one_job(self, zeebe_worker, task, job_from_task, get_jobs_mock):
        get_jobs_mock.return_value = [job_from_task]

        zeebe_worker._handle_jobs(task)

        task.handler.assert_called_with(job_from_task)

    def test_handle_many_jobs(self, zeebe_worker, task, job_from_task, get_jobs_mock):
        get_jobs_mock.return_value = [job_from_task] * 10

        zeebe_worker._handle_jobs(task)

        assert task.handler.call_count == 10


class TestWorkerThreads:
    def test_work_thread_start_called(self, zeebe_worker, task):
        with patch("pyzeebe.worker.worker.Thread") as thread_mock:
            thread_instance_mock = MagicMock()
            thread_mock.return_value = thread_instance_mock
            zeebe_worker._add_task(task)
            zeebe_worker.work()
            zeebe_worker.stop()
            thread_instance_mock.start.assert_called_once()

    def test_stop_worker(self, zeebe_worker):
        zeebe_worker.work()
        zeebe_worker.stop()

    def test_watch_task_threads_dont_restart_running_threads(
            self, zeebe_worker, task, handle_task_mock, stop_event_mock, handle_not_alive_thread_spy, stop_after_test):
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
            self, zeebe_worker, task, handle_task_mock, stop_event_mock, handle_not_alive_thread_spy):
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


class TestGetJobs:
    def test_activate_jobs_called(self, zeebe_worker, task):
        zeebe_worker.zeebe_adapter.activate_jobs = MagicMock()
        zeebe_worker._get_jobs(task)
        zeebe_worker.zeebe_adapter.activate_jobs.assert_called_with(task_type=task.type, worker=zeebe_worker.name,
                                                                    timeout=task.timeout,
                                                                    max_jobs_to_activate=task.max_jobs_to_activate,
                                                                    variables_to_fetch=task.variables_to_fetch,
                                                                    request_timeout=zeebe_worker.request_timeout)


class TestIncludeRouter:
    def test_include_router_adds_task(self, zeebe_worker, router, task_type):
        self.include_router_with_task(zeebe_worker, router, task_type)

        assert zeebe_worker.get_task(task_type) is not None

    def test_include_multiple_routers(self, zeebe_worker, routers):
        for router in routers:
            self.include_router_with_task(zeebe_worker, router)

        assert len(zeebe_worker.tasks) == len(routers)

    def test_router_before_decorator(self, zeebe_worker, router, decorator, job_without_adapter):
        router.before(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        task.handler(job_without_adapter)

        assert decorator.call_count == 1

    def test_router_after_decorator(self, zeebe_worker, router, decorator, job_without_adapter):
        router.after(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        task.handler(job_without_adapter)

        assert decorator.call_count == 1

    @staticmethod
    def include_router_with_task(zeebe_worker, router, task_type=None):
        task_type = task_type or str(uuid4())

        @router.task(task_type)
        def _(x):
            return dict(x=x)

        zeebe_worker.include_router(router)
        return zeebe_worker.get_task(task_type)
