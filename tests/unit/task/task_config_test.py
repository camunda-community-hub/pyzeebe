from unittest.mock import patch
from uuid import uuid4

import pytest

from pyzeebe import Job
from pyzeebe.errors import NoVariableNameGivenError
from pyzeebe.task.task_config import TaskConfig, default_exception_handler


def test_add_dict_task_with_correct_parameters(task_type: str):
    expected_config_as_dict = {
        "type": task_type,
        "exception_handler": default_exception_handler,
        "timeout_ms": 10000,
        "max_jobs_to_activate": 32,
        "variables_to_fetch": None,
        "single_value": False,
        "variable_name": None,
        "before": [],
        "after": []
    }

    config = TaskConfig(task_type)

    assert config.__dict__ == expected_config_as_dict


def test_add_non_dict_task_without_variable_name():
    with pytest.raises(NoVariableNameGivenError):
        TaskConfig(str(uuid4()), single_value=True)


def test_default_exception_handler_logs_a_warning(mocked_job_with_adapter: Job):
    with patch("pyzeebe.task.task_config.logger.warning") as logging_mock:
        default_exception_handler(Exception(), mocked_job_with_adapter)

        mocked_job_with_adapter.set_failure_status.assert_called()
        logging_mock.assert_called()
