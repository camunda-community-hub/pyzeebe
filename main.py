from typing import Dict

from pyz.task.task import Task
from pyz.task.task_context import TaskContext
from pyz.worker.worker import ZeebeWorker


def handler(input: str) -> Dict[str, str]:
    print("handling", input)
    return {"output": f"Hello World, {input}!"}


def on_error(e: Exception, context: TaskContext) -> None:
    print(e)
    print(context)


if __name__ == '__main__':
    worker = ZeebeWorker(hostname='localhost', port=26500, request_timeout=60000, name='test')
    worker.add_task(
        Task('echo', handler, on_error, variables_to_fetch=['input'], max_jobs_to_activate=32, timeout=1000))
    worker.work()
