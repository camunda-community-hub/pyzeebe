import pytest

from pyzeebe.worker.task_state import TaskState


@pytest.fixture
def task_state():
    return TaskState()


def test_new_task_state_has_0_active_jobs(task_state):
    assert task_state.count_active() == 0


def test_add_counts_as_active(task_state, job_from_task):
    task_state.add(job_from_task)
    assert task_state.count_active() == 1


def test_add_then_remove_results_in_0_active(task_state, job_from_task):
    task_state.add(job_from_task)
    task_state.remove(job_from_task)
    assert task_state.count_active() == 0


def test_prevents_adding_duplicate_job(task_state, job_from_task):
    with pytest.raises(ValueError) as exc_info:
        for _ in range(2):
            task_state.add(job_from_task)
    assert exc_info.value.args[0].endswith("already registered in TaskState")


def test_remove_non_existing_job_dont_withdraw_from_active_jobs(task_state, job_from_task):
    task_state.remove(job_from_task)
    assert task_state.count_active() == 0
