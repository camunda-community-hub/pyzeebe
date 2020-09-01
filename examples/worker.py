import logging
from typing import Dict

from pyzeebe import Task, TaskContext, TaskStatusController, ZeebeWorker

logging.basicConfig(level=logging.DEBUG)

def example_task() -> Dict:
    return {'output': f'Hello world, test!'}


def example_exception_handler(exc: Exception, context: TaskContext, controller: TaskStatusController) -> None:
    print(exc)
    print(context)
    controller.error(f'Failed to run task {context.type}. Reason: {exc}')


task = Task(task_type='test', task_handler=example_task, exception_handler=example_exception_handler)
task_2 = Task(task_type='test2', task_handler=example_task, exception_handler=example_exception_handler)

worker = ZeebeWorker()  # Will use environment variable ZEEBE_ADDRESS or localhost:26500

worker.add_task(task)

if __name__ == '__main__':
    worker.work()
