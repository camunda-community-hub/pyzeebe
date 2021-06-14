import pytest

from pyzeebe.function_tools import dict_tools


@pytest.mark.asyncio
class TestConvertToDictFunction:
    async def test_converting_to_dict(self):
        async def original_function(x):
            return x

        dict_function = dict_tools.convert_to_dict_function(
            original_function, "x"
        )

        assert {"x": 1} == await dict_function(1)
