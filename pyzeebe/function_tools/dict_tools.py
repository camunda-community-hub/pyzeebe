import functools

from pyzeebe.function_tools import AsyncFunction, DictFunction


def convert_to_dict_function(single_value_function: AsyncFunction, variable_name: str) -> DictFunction:
    @functools.wraps(single_value_function)
    async def inner_fn(*args, **kwargs):
        return {variable_name: await single_value_function(*args, **kwargs)}

    return inner_fn
