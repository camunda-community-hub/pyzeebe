from unittest import mock
from uuid import uuid4

import pytest

from pyzeebe.errors import BusinessError, DuplicateTaskTypeError, TaskNotFoundError
from pyzeebe.job.job import Job, JobController
from pyzeebe.task.exception_handler import default_exception_handler
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
    with pytest.raises(DuplicateTaskTypeError):
        router._is_task_duplicate(task.type)


def test_no_duplicate_task_type_error_is_raised(router: ZeebeTaskRouter, task: Task):
    router._is_task_duplicate(task.type)


@pytest.mark.asyncio
async def test_default_exception_handler_logs_a_warning(job: Job, mocked_job_controller: JobController):
    with mock.patch("pyzeebe.task.exception_handler.logger.warning") as logging_mock:
        await default_exception_handler(Exception(), job, mocked_job_controller)

        mocked_job_controller.set_failure_status.assert_called()
        logging_mock.assert_called()


@pytest.mark.asyncio
async def test_default_exception_handler_uses_business_error(job: Job, mocked_job_controller: JobController):
    error_code = "custom-error-code"
    exception = BusinessError(error_code)
    await default_exception_handler(exception, job, mocked_job_controller)
    mocked_job_controller.set_error_status.assert_called_with(mock.ANY, error_code=error_code)


@pytest.mark.asyncio
async def test_default_exception_handler_warns_of_job_failure(job: Job, mocked_job_controller: JobController):
    with mock.patch("pyzeebe.task.exception_handler.logger.warning") as logging_mock:
        exception = BusinessError("custom-error-code")
        await default_exception_handler(exception, job, mocked_job_controller)
        logging_mock.assert_called()
