from typing import Callable, List

import pytest

from pyzeebe.function_tools import parameter_tools
from pyzeebe.job.job import Job
from tests.unit.utils import dummy_functions


class TestGetFunctionParameters:
    @pytest.mark.parametrize("fn,expected", [
        (dummy_functions.no_param, []),
        (dummy_functions.one_param, ["x"]),
        (dummy_functions.multiple_params, ["x", "y", "z"]),
        (dummy_functions.one_keyword_param, ["x"]),
        (dummy_functions.multiple_keyword_param, ["x", "y", "z"]),
        (dummy_functions.positional_and_keyword_params, ["x", "y"]),
        (dummy_functions.args_param, []),
        (dummy_functions.kwargs_param, []),
        (dummy_functions.standard_named_params, ["args", "kwargs"]),
        (dummy_functions.lambda_no_params, []),
        (dummy_functions.lambda_one_param, ["x"]),
        (dummy_functions.lambda_multiple_params, ["x", "y", "z"]),
        (dummy_functions.lambda_one_keyword_param, ["x"]),
        (dummy_functions.lambda_multiple_keyword_params, ["x", "y", "z"]),
        (dummy_functions.lambda_positional_and_keyword_params, ["x", "y"])
    ])
    def test_get_params(self, fn: Callable, expected: List[str]):
        assert parameter_tools.get_parameters_from_function(fn) == expected


class TestGetJobParameter:
    def test_returns_none_when_there_are_no_parameters_annotated_with_job(self):
        job_parameter = parameter_tools.get_job_parameter_name(
            dummy_functions.multiple_params)

        assert job_parameter == None

    def test_returns_parameter_name_when_annotated(self):
        job_parameter = parameter_tools.get_job_parameter_name(
            dummy_functions.with_job_parameter)

        assert job_parameter == "job"

    def test_returns_first_parameter_annotated_with_job(self):
        job_parameter = parameter_tools.get_job_parameter_name(
            dummy_functions.with_multiple_job_parameters)

        assert job_parameter == "job"
