from typing import Dict

from zeebepy import Task, TaskContext, TaskStatusController, ZeebeWorker


def example_task(input: str) -> Dict:
    return {'output': f'Hello world, {input}!'}


def example_exception_handler(exc: Exception, context: TaskContext, controller: TaskStatusController) -> None:
    print(exc)
    print(context)
    controller.error(f'Failed to run task {context.type}. Reason: {exc}')


task = Task(task_type='example', task_handler=example_task, exception_handler=example_exception_handler)

worker = ZeebeWorker()  # Will use environment variable ZEEBE_ADDRESS or localhost:26500

worker.add_task(task)

if __name__ == '__main__':
    worker.work()
