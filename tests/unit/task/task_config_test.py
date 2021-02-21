from uuid import uuid4

import pytest

from pyzeebe.exceptions import NoVariableNameGiven
from pyzeebe.task.task_config import TaskConfig


def test_add_non_dict_task_without_variable_name():
    with pytest.raises(NoVariableNameGiven):
        TaskConfig(str(uuid4()), single_value=True)
