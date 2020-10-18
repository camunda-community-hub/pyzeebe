from random import randint
from threading import Thread
from unittest.mock import patch, MagicMock
from uuid import uuid4

from pyzeebe.exceptions import DuplicateTaskType
from pyzeebe.job.job import Job
from pyzeebe.task.task import Task
from pyzeebe.worker.task_router import ZeebeTaskRouter
from pyzeebe.worker.worker import ZeebeWorker
from tests.unit.utils.grpc_utils import *
from tests.unit.utils.random_utils import random_job

zeebe_worker: ZeebeWorker
task: Task


def decorator(job: Job) -> Job:
    return job


@pytest.fixture(autouse=True)
def run_around_tests():
    global zeebe_worker, task
    task = Task(str(uuid4()), lambda x: {"x": x}, lambda x, y, z: x)
    zeebe_worker = ZeebeWorker()
    yield
    zeebe_worker = ZeebeWorker()
    task = Task(str(uuid4()), lambda x: {"x": x}, lambda x, y, z: x)


def test_add_task():
    zeebe_worker._add_task(task)

    assert len(zeebe_worker.tasks) == 1
    assert zeebe_worker.get_task(task.type) == task


def test_add_duplicate_task():
    zeebe_worker._add_task(task)
    with pytest.raises(DuplicateTaskType):
        zeebe_worker._add_task(task)


def test_add_task_through_decorator():
    task_type = str(uuid4())
    timeout = randint(0, 10000)
    max_jobs_to_activate = randint(0, 1000)

    @zeebe_worker.task(task_type=task_type, timeout=timeout, max_jobs_to_activate=max_jobs_to_activate)
    def example_test_task(x):
        return {"x": x}

    assert len(zeebe_worker.tasks) == 1
    assert zeebe_worker.get_task(task_type).handler is not None

    variable = str(uuid4())
    assert example_test_task(variable) == {"x": variable}

    global task
    task = zeebe_worker.get_task(task_type)
    assert task is not None

    variable = str(uuid4())
    assert task.inner_function(variable) == {"x": variable}
    assert task.variables_to_fetch == ["x"]
    assert task.timeout == timeout
    assert task.max_jobs_to_activate == max_jobs_to_activate

    assert callable(task.handler)
    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}
    with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as mock:
        assert isinstance(task.handler(job), Job)
        mock.assert_called_with(job_key=job.key, variables=job.variables)


def test_add_task():
    zeebe_worker._add_task(task)
    assert len(zeebe_worker.tasks) == 1
    assert zeebe_worker.get_task(task.type).handler is not None

    variable = str(uuid4())
    assert task.inner_function(variable) == {"x": variable}

    assert callable(task.handler)
    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}
    with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as mock:
        assert isinstance(task.handler(job), Job)
        mock.assert_called_with(job_key=job.key, variables=job.variables)


def test_before_task_decorator_called():
    with patch("tests.unit.worker.worker_test.decorator") as mock:
        job = random_job(task=task)
        job.variables = {"x": str(uuid4())}

        mock.return_value = job

        task.before(decorator)
        zeebe_worker._add_task(task)
        with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as grpc_mock:
            assert isinstance(task.handler(job), Job)
            grpc_mock.assert_called_with(job_key=job.key, variables=job.variables)
        mock.assert_called_with(job)


def test_after_task_decorator_called():
    with patch("tests.unit.worker.worker_test.decorator") as mock:
        job = random_job(task=task)
        job.variables = {"x": str(uuid4())}

        mock.return_value = job

        task.after(decorator)
        zeebe_worker._add_task(task)

        with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as grpc_mock:
            assert isinstance(task.handler(job), Job)
            grpc_mock.assert_called_with(job_key=job.key, variables=job.variables)
        mock.assert_called_with(job)


def test_decorator_failed():
    job = random_job(task=task)

    with patch("tests.unit.worker.worker_test.decorator") as decorator_mock:
        decorator_mock.side_effect = Exception()
        zeebe_worker.before(decorator)
        zeebe_worker.after(decorator)
        zeebe_worker._add_task(task)

        assert isinstance(task.handler(job), Job)
        assert decorator_mock.call_count == 2


def test_task_exception_handler_called():
    def task_handler(x):
        raise Exception()

    def exception_handler(e, job, status_setter):
        pass

    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}

    task.inner_function = task_handler
    task.exception_handler = exception_handler

    with patch("tests.unit.worker.worker_test.task.exception_handler") as mock:
        zeebe_worker._add_task(task)
        task.handler(job)
        mock.assert_called()


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
    job = random_job(task=task)
    job.variables = {"x": str(uuid4())}
    decorators = zeebe_worker._create_before_decorator_runner(task)
    assert isinstance(decorators(job), Job)


def test_handle_one_job():
    job = random_job(task=task)

    with patch("pyzeebe.worker.worker.ZeebeWorker._get_jobs") as get_jobs_mock:
        get_jobs_mock.return_value = [job]
        with patch("tests.unit.worker.worker_test.task.handler") as task_handler_mock:
            task_handler_mock.return_value = {"x": str(uuid4())}
            zeebe_worker._handle_jobs(task)
            task_handler_mock.assert_called_with(job)


def test_handle_no_job():
    job = random_job(task=task)

    with patch("pyzeebe.worker.worker.ZeebeWorker._get_jobs") as get_jobs_mock:
        get_jobs_mock.return_value = []
        with patch("tests.unit.worker.worker_test.task.handler") as task_handler_mock:
            task_handler_mock.return_value = {"x": str(uuid4())}
            zeebe_worker._handle_jobs(task)
            with pytest.raises(AssertionError):
                task_handler_mock.assert_called_with(job)


def test_handle_many_jobs():
    job = random_job(task=task)

    with patch("pyzeebe.worker.worker.ZeebeWorker._get_jobs") as get_jobs_mock:
        get_jobs_mock.return_value = [job]
        with patch("tests.unit.worker.worker_test.task.handler") as task_handler_mock:
            task_handler_mock.return_value = {"x": str(uuid4())}
            zeebe_worker._handle_jobs(task)
            task_handler_mock.assert_called_with(job)


def test_work_thread_start_called():
    Thread.start = MagicMock()
    zeebe_worker._add_task(task)
    zeebe_worker.work()
    zeebe_worker.stop()
    Thread.start.assert_called_once()


def test_stop_worker():
    zeebe_worker.work()
    zeebe_worker.stop()


def test_include_router():
    task_type = str(uuid4())
    router = ZeebeTaskRouter()

    @router.task(task_type=task_type)
    def task_fn(x):
        return {"x": x}

    zeebe_worker.include_router(router)
    assert zeebe_worker.get_task(task_type) is not None


def test_include_multiple_routers():
    routers = [ZeebeTaskRouter() for _ in range(0, randint(2, 100))]

    for router in routers:
        task_type = str(uuid4())

        @router.task(task_type=task_type)
        def task_fn(x):
            return {"x": x}

        zeebe_worker.include_router(router)

    assert len(zeebe_worker.tasks) == len(routers)


def test_router_before_decorator():
    with patch("tests.unit.worker.worker_test.decorator") as mock:
        task_type = str(uuid4())
        router = ZeebeTaskRouter()
        router.before(decorator)

        @router.task(task_type=task_type, before=[decorator])
        def task_fn(x):
            return {"x": x}

        zeebe_worker.before(decorator)
        zeebe_worker.include_router(router)

        task = zeebe_worker.get_task(task_type)

        job = random_job(task=task)
        job.variables = {"x": str(uuid4())}

        mock.return_value = job

        with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as grpc_mock:
            assert isinstance(task.handler(job), Job)
            grpc_mock.assert_called_with(job_key=job.key, variables=job.variables)

        assert mock.call_count == 3


def test_router_after_decorator():
    with patch("tests.unit.worker.worker_test.decorator") as mock:
        task_type = str(uuid4())
        router = ZeebeTaskRouter()
        router.after(decorator)

        @router.task(task_type=task_type, after=[decorator])
        def task_fn(x):
            return {"x": x}

        zeebe_worker.after(decorator)
        zeebe_worker.include_router(router)

        task = zeebe_worker.get_task(task_type)

        job = random_job(task=task)
        job.variables = {"x": str(uuid4())}

        mock.return_value = job

        with patch("pyzeebe.grpc_internals.zeebe_adapter.ZeebeAdapter.complete_job") as grpc_mock:
            assert isinstance(task.handler(job), Job)
            grpc_mock.assert_called_with(job_key=job.key, variables=job.variables)

        assert mock.call_count == 3


def test_router_non_dict_task():
    with patch("pyzeebe.worker.task_handler.ZeebeTaskHandler._single_value_function_to_dict") as single_value_mock:
        task_type = str(uuid4())
        variable_name = str(uuid4())

        @zeebe_worker.task(task_type=task_type, single_value=True, variable_name=variable_name)
        def task_fn(x):
            return {"x": x}

        single_value_mock.assert_called_with(variable_name=variable_name, fn=task_fn)
    assert len(zeebe_worker.tasks) == 1


def test_get_jobs():
    zeebe_worker.zeebe_adapter.activate_jobs = MagicMock()
    zeebe_worker._get_jobs(task)
    zeebe_worker.zeebe_adapter.activate_jobs.assert_called_with(task_type=task.type, worker=zeebe_worker.name,
                                                                timeout=task.timeout,
                                                                max_jobs_to_activate=task.max_jobs_to_activate,
                                                                variables_to_fetch=task.variables_to_fetch,
                                                                request_timeout=zeebe_worker.request_timeout)
