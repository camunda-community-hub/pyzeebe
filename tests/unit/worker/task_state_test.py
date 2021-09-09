import pytest

from pyzeebe.job.job import Job
from pyzeebe.worker.task_state import TaskState


@pytest.fixture
def task_state():
    return TaskState()


def test_new_task_state_has_0_active_jobs(task_state: TaskState):
    assert task_state.count_active() == 0


def test_add_counts_as_active(task_state: TaskState, job_from_task):
    task_state.add(job_from_task)
    assert task_state.count_active() == 1


def test_add_then_remove_results_in_0_active(task_state: TaskState, job_from_task: Job):
    task_state.add(job_from_task)
    task_state.remove(job_from_task)
    assert task_state.count_active() == 0


def test_remove_non_existing_job_dont_withdraw_from_active_jobs(
    task_state: TaskState, job_from_task: Job
):
    task_state.remove(job_from_task)
    assert task_state.count_active() == 0


def test_add_already_activated_job_does_not_raise_an_error(
    task_state: TaskState, job_from_task: Job
):
    task_state.add(job_from_task)
    task_state.add(job_from_task)
