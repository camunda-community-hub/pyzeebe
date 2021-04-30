import time
from random import randint
from threading import Event as StopEvent
from typing import List
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest

from pyzeebe import TaskDecorator, ZeebeTaskRouter
from pyzeebe.errors import DuplicateTaskTypeError, MaxConsecutiveTaskThreadError
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.worker import ZeebeWorker


class TestAddTask:
    def test_add_task(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type) == task

    def test_raises_on_duplicate(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)
        with pytest.raises(DuplicateTaskTypeError):
            zeebe_worker._add_task(task)

    def test_only_one_task_added(self, zeebe_worker: ZeebeWorker):
        @zeebe_worker.task(str(uuid4()))
        def dummy_function():
            pass

        assert len(zeebe_worker.tasks) == 1

    def test_task_type_saved(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker._add_task(task)

        assert zeebe_worker.get_task(task.type).type == task.type

    def test_variables_to_fetch_match_function_parameters(self, zeebe_worker: ZeebeWorker, task_type: str):
        expected_variables_to_fetch = ["x"]

        @zeebe_worker.task(task_type)
        def dummy_function(x):
            pass

        assert zeebe_worker.get_task(
            task_type).config.variables_to_fetch == expected_variables_to_fetch


class TestDecorator:
    def test_add_before_decorator(self, zeebe_worker: ZeebeWorker, decorator: TaskDecorator):
        zeebe_worker.before(decorator)
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    def test_add_after_decorator(self, zeebe_worker: ZeebeWorker, decorator: TaskDecorator):
        zeebe_worker.after(decorator)
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after

    def test_add_constructor_before_decorator(self, decorator: TaskDecorator):
        zeebe_worker = ZeebeWorker(before=[decorator])
        assert len(zeebe_worker._before) == 1
        assert decorator in zeebe_worker._before

    def test_add_constructor_after_decorator(self, decorator: TaskDecorator):
        zeebe_worker = ZeebeWorker(after=[decorator])
        assert len(zeebe_worker._after) == 1
        assert decorator in zeebe_worker._after


class TestHandleJobs:
    @pytest.fixture(autouse=True)
    def get_jobs_mock(self, zeebe_worker: ZeebeWorker):
        zeebe_worker._get_jobs = MagicMock()
        return zeebe_worker._get_jobs

    @pytest.fixture(autouse=True)
    def job_handler_spy(self, task: Task):
        task.job_handler = MagicMock(wraps=task.job_handler)

    def test_handle_no_job(self, zeebe_worker: ZeebeWorker, task: Task, get_jobs_mock: MagicMock):
        get_jobs_mock.return_value = []

        zeebe_worker._handle_jobs(task)

        task.job_handler.assert_not_called()

    def test_handle_one_job(self, zeebe_worker: ZeebeWorker, task: Task, job_from_task: Job, get_jobs_mock: MagicMock):
        get_jobs_mock.return_value = [job_from_task]

        zeebe_worker._handle_jobs(task)

        task.job_handler.assert_called_with(job_from_task, zeebe_worker._task_state)

    def test_handle_many_jobs(self, zeebe_worker: ZeebeWorker, task: Task, job_from_task: Job,
                              get_jobs_mock: MagicMock):
        get_jobs_mock.return_value = [job_from_task] * 10

        zeebe_worker._handle_jobs(task)

        assert task.job_handler.call_count == 10


class TestWorkerThreads:
    def test_work_thread_start_called(self, zeebe_worker: ZeebeWorker, task: Task):
        with patch("pyzeebe.worker.worker.Thread") as thread_mock:
            thread_instance_mock = MagicMock()
            thread_mock.return_value = thread_instance_mock
            zeebe_worker._add_task(task)
            zeebe_worker.work()
            zeebe_worker.stop()
            thread_instance_mock.start.assert_called_once()

    def test_stop_worker(self, zeebe_worker: ZeebeWorker):
        zeebe_worker.work()
        zeebe_worker.stop()

    def test_watch_task_threads_dont_restart_running_threads(
            self, zeebe_worker: ZeebeWorker, task: Task, handle_task_mock: MagicMock, stop_event_mock: MagicMock,
            handle_not_alive_thread_spy: MagicMock, stop_after_test: StopEvent):
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
            self, zeebe_worker: ZeebeWorker, task: Task, handle_task_mock: MagicMock, stop_event_mock: MagicMock,
            handle_not_alive_thread_spy: MagicMock):
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
    def test_activate_jobs_called(self, zeebe_worker: ZeebeWorker, task: Task):
        zeebe_worker.zeebe_adapter.activate_jobs = MagicMock()
        zeebe_worker._get_jobs(task)
        zeebe_worker.zeebe_adapter.activate_jobs.assert_called_with(task_type=task.type, worker=zeebe_worker.name,
                                                                    timeout=task.config.timeout_ms,
                                                                    max_jobs_to_activate=zeebe_worker.max_task_count,
                                                                    variables_to_fetch=task.config.variables_to_fetch,
                                                                    request_timeout=zeebe_worker.request_timeout)


class TestIncludeRouter:
    def test_include_router_adds_task(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str):
        self.include_router_with_task(zeebe_worker, router, task_type)

        assert zeebe_worker.get_task(task_type) is not None

    def test_include_multiple_routers(self, zeebe_worker: ZeebeWorker, routers: List[ZeebeTaskRouter]):
        for router in routers:
            self.include_router_with_task(zeebe_worker, router)

        assert len(zeebe_worker.tasks) == len(routers)

    def test_router_before_decorator(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, decorator: TaskDecorator,
                                     mocked_job_with_adapter: Job):
        router.before(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        task.job_handler(mocked_job_with_adapter)

        decorator.assert_called_once()

    def test_router_after_decorator(self, zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, decorator: TaskDecorator,
                                    mocked_job_with_adapter: Job):
        router.after(decorator)
        task = self.include_router_with_task(zeebe_worker, router)

        task.job_handler(mocked_job_with_adapter)

        decorator.assert_called_once()

    @staticmethod
    def include_router_with_task(zeebe_worker: ZeebeWorker, router: ZeebeTaskRouter, task_type: str = None) -> Task:
        task_type = task_type or str(uuid4())

        @router.task(task_type)
        def dummy_function():
            return {}

        zeebe_worker.include_router(router)
        return zeebe_worker.get_task(task_type)


class TestWorkerMaxTasks:
    default_max_jobs_to_activate = 32 # on task.config.max_jobs_to_activate

    @pytest.mark.parametrize("max_task_count,expected", [(64, default_max_jobs_to_activate), (16, 16)])
    def test_set_worker_with_max_task_count_activates_max(self, max_task_count, expected,
                                                          zeebe_worker: ZeebeWorker, task: Task):
        activate_job_mock = MagicMock()
        zeebe_worker.zeebe_adapter.activate_jobs = activate_job_mock
        zeebe_worker.max_task_count = max_task_count

        zeebe_worker._get_jobs(task)

        assert activate_job_mock.call_args[1]["max_jobs_to_activate"] == expected

    def test_activating_jobs_increase_and_decrease_active_task_count(self, zeebe_worker: ZeebeWorker,
                                                                     job_from_task: Job, task: Task):
        zeebe_worker.max_task_count = 10
        num_jobs_activated = randint(4, 10)
        jobs = [job_from_task for _ in range(num_jobs_activated)]
        activate_job_mock = MagicMock(return_value=jobs)
        zeebe_worker.zeebe_adapter.activate_jobs = activate_job_mock
        with patch.object(zeebe_worker, "_task_state", wraps=zeebe_worker._task_state) as task_state_spy:
            zeebe_worker._handle_jobs(task)

            assert task_state_spy.add.call_count == num_jobs_activated
            assert task_state_spy.remove.call_count == num_jobs_activated

    calculate_max_jobs_to_activate_cases = dict(
        max_task_count_minus_active_decides=(4, 10, 12, 6),
        max_task_count_minus_active_decides_2=(4, 12, 10, 8),
        max_task_count_minus_active_decides_zero_free=(4, 4, 12, 0),
        max_jobs_to_activate_decides=(4, 10, 5, 5),
        max_jobs_to_activate_decides_zero_active=(0, 10, 5, 5)
    )

    @pytest.mark.parametrize("active_jobs,max_task_count,max_jobs_to_activate,expected",
                             calculate_max_jobs_to_activate_cases.values(),
                             ids=calculate_max_jobs_to_activate_cases.keys())
    def test_calculate_max_jobs_to_activate(self, zeebe_worker: ZeebeWorker, active_jobs,
                                            max_task_count, max_jobs_to_activate, expected):
        zeebe_worker.max_task_count = max_task_count
        for i in range(active_jobs):
            mock_job = MagicMock()
            mock_job.key = i
            zeebe_worker._task_state.add(mock_job)

        result = zeebe_worker._calculate_max_jobs_to_activate(max_jobs_to_activate)

        assert result == expected
