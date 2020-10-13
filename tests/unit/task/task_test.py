import uuid
from unittest.mock import patch

from pyzeebe.task.task import Task, default_exception_handler
from tests.unit.utils.random_utils import random_job


def test_add_before():
    base_decorator = Task(task_type=str(uuid.uuid4()), task_handler=lambda x: x, exception_handler=lambda x: x)
    base_decorator.before(lambda x: x)
    assert len(base_decorator._before) == 1


def test_add_after():
    base_decorator = Task(task_type=str(uuid.uuid4()), task_handler=lambda x: x, exception_handler=lambda x: x)
    base_decorator.after(lambda x: x)
    assert len(base_decorator._after) == 1


def test_add_before_plus_constructor():
    def constructor_decorator(x):
        return x + 1

    def function_decorator(x):
        return x

    base_decorator = Task(task_type=str(uuid.uuid4()), task_handler=lambda x: x, exception_handler=lambda x: x,
                          before=[constructor_decorator])
    base_decorator.before(function_decorator)
    assert len(base_decorator._before) == 2
    assert base_decorator._before == [constructor_decorator, function_decorator]


def test_add_after_plus_constructor():
    def constructor_decorator(x):
        return x + 1

    def function_decorator(x):
        return x

    base_decorator = Task(task_type=str(uuid.uuid4()), task_handler=lambda x: x, exception_handler=lambda x: x,
                          after=[constructor_decorator])
    base_decorator.after(function_decorator)
    assert len(base_decorator._after) == 2
    assert base_decorator._after == [constructor_decorator, function_decorator]


def test_default_exception_handler():
    with patch("logging.warning") as logging_mock:
        with patch("pyzeebe.job.job.Job.set_failure_status") as failure_mock:
            failure_mock.return_value = None
            job = random_job()
            default_exception_handler(Exception(), job)

            failure_mock.assert_called()
        logging_mock.assert_called()
