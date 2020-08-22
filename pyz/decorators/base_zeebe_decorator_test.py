from pyz.common.test_utils import random_job_context
from pyz.decorators.base_zeebe_decorator import BaseZeebeDecorator


def test_add_before():
    base_decorator = BaseZeebeDecorator()
    base_decorator.before(lambda x: x)
    assert len(base_decorator._before) == 1


def test_add_after():
    base_decorator = BaseZeebeDecorator()
    base_decorator.after(lambda x: x)
    assert len(base_decorator._after) == 1


def test_add_before_plus_constructor():
    def constructor_decorator(x):
        return x

    def function_decorator(x):
        return x

    context = random_job_context()

    assert constructor_decorator(context) == context
    assert function_decorator(context) == context

    base_decorator = BaseZeebeDecorator(before=[constructor_decorator])
    base_decorator.before(function_decorator)
    assert len(base_decorator._before) == 2
    assert base_decorator._before == [constructor_decorator, function_decorator]


def test_add_after_plus_constructor():
    def constructor_decorator(x):
        return x

    def function_decorator(x):
        return x

    context = random_job_context()

    assert constructor_decorator(context) == context
    assert function_decorator(context) == context

    base_decorator = BaseZeebeDecorator(after=[constructor_decorator])
    base_decorator.after(function_decorator)
    assert len(base_decorator._after) == 2
    assert base_decorator._after == [constructor_decorator, function_decorator]
