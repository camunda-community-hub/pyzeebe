from pyzeebe.common.random_utils import random_task_context
from pyzeebe.decorators.zeebe_decorator_base import ZeebeDecoratorBase


def test_add_before():
    base_decorator = ZeebeDecoratorBase()
    base_decorator.before(lambda x: x)
    assert len(base_decorator._before) == 1


def test_add_after():
    base_decorator = ZeebeDecoratorBase()
    base_decorator.after(lambda x: x)
    assert len(base_decorator._after) == 1


def test_add_before_plus_constructor():
    def constructor_decorator(x):
        return x

    def function_decorator(x):
        return x

    context = random_task_context()

    assert constructor_decorator(context) == context
    assert function_decorator(context) == context

    base_decorator = ZeebeDecoratorBase(before=[constructor_decorator])
    base_decorator.before(function_decorator)
    assert len(base_decorator._before) == 2
    assert base_decorator._before == [constructor_decorator, function_decorator]


def test_add_after_plus_constructor():
    def constructor_decorator(x):
        return x

    def function_decorator(x):
        return x

    context = random_task_context()

    assert constructor_decorator(context) == context
    assert function_decorator(context) == context

    base_decorator = ZeebeDecoratorBase(after=[constructor_decorator])
    base_decorator.after(function_decorator)
    assert len(base_decorator._after) == 2
    assert base_decorator._after == [constructor_decorator, function_decorator]
