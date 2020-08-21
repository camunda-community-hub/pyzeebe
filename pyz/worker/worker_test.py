import uuid

import pytest

from pyz.exceptions import TaskNotFoundException
from pyz.task import Task
from pyz.worker import ZeebeWorker


class TestZeebeWorker:
    def setup_class(self):
        self.zeebe_worker = ZeebeWorker()

    def _add_zeebe_task(self) -> str:
        task_type = str(uuid.uuid4())
        self.zeebe_worker.add_task(Task(task_type, lambda x: x, lambda x: x))
        return task_type

    def test_add_task(self):
        task_type = self._add_zeebe_task()
        assert (self.zeebe_worker.get_task(task_type) is not None)

    def test_remove_task(self):
        task_type = self._add_zeebe_task()
        assert (self.zeebe_worker.remove_task(task_type) is not None)
        with pytest.raises(TaskNotFoundException):
            self.zeebe_worker.get_task(task_type)

    def test_add_decorator(self):
        self.zeebe_worker = ZeebeWorker(before=[lambda x: x])
        print(self.zeebe_worker._before)
        assert (len(self.zeebe_worker._before) == 1)
