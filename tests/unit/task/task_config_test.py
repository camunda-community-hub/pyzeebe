from typing import Callable, List

from pyzeebe.function_tools import async_tools
from pyzeebe.job.job import Job
from pyzeebe.task.task_config import TaskConfig
from tests.unit.utils.function_tools import functions_are_all_async


class TestConstructor:
    async def async_decorator(self, job: Job) -> Job:
        return job

    def sync_decorator(self, job: Job) -> Job:
        return job

    def exception_handler(self, ):
        pass

    def test_before_decorators_are_async(self, task_type: str):
        task_config = TaskConfig(
            task_type,
            self.exception_handler,
            10000,
            32,
            32,
            [],
            False,
            "",
            [self.sync_decorator, self.async_decorator],
            []
        )

        assert functions_are_all_async(task_config.before)

    def test_after_decorators_are_async(self, task_type: str):
        task_config = TaskConfig(
            task_type,
            self.exception_handler,
            10000,
            32,
            32,
            [],
            False,
            "",
            [],
            [self.sync_decorator, self.async_decorator]
        )

        assert functions_are_all_async(task_config.after)
