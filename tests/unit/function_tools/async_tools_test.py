import inspect
from typing import Callable, List

import pytest

from pyzeebe.function_tools import async_tools
from tests.unit.utils.function_tools import functions_are_all_async


class TestAsyncify:
    def test_returns_async_function(self):
        async_function = async_tools.asyncify(lambda x: x)

        assert inspect.iscoroutinefunction(async_function)

    @pytest.mark.asyncio
    async def test_returned_function_returns_expected_value(self):
        expected_result = 5
        async_function = async_tools.asyncify(lambda: expected_result)

        assert await async_function() == expected_result

    @pytest.mark.asyncio
    async def test_returned_function_accepts_keyword_arguments(self):
        async_function = async_tools.asyncify(lambda x, y, z: x + y + z)

        assert await async_function(x=1, y=1, z=1) == 3


class TestAsyncifyAllFunctions:
    def sync_function(self):
        return

    async def async_function(self):
        return

    def test_changes_sync_function(self):
        functions = [self.sync_function]

        async_functions = async_tools.asyncify_all_functions(functions)

        assert functions_are_all_async(async_functions)

    def test_async_function_remains_unchanged(self):
        functions = [self.async_function]

        async_functions = async_tools.asyncify_all_functions(functions)

        assert async_functions[0] == functions[0]


class TestIsAsyncFunction:
    def test_with_normal_function(self):
        def normal_function():
            return 1

        assert not async_tools.is_async_function(normal_function)

    def test_with_async_function(self):
        async def async_function():
            return 1

        assert async_tools.is_async_function(async_function)
