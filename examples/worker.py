from typing import Dict

from pyzeebe import Task, TaskContext, TaskStatusController, ZeebeWorker, CamundaCloudCredentials


def example_task() -> Dict:
    return {"output": f"Hello world, test!"}


def example_exception_handler(exc: Exception, context: TaskContext, controller: TaskStatusController) -> None:
    print(exc)
    print(context)
    controller.error(f"Failed to run task {context.type}. Reason: {exc}")


task = Task(task_type="test", task_handler=example_task, exception_handler=example_exception_handler)


# Use decorators to add functionality before and after tasks. These will not fail the task
def example_logging_task_decorator(task_context: TaskContext) -> TaskContext:
    print(task_context)
    return task_context


task.before(example_logging_task_decorator)
task.after(example_logging_task_decorator)

# Will use environment variable ZEEBE_ADDRESS or localhost:26500 and NOT use TLS
worker = ZeebeWorker()

# Will use environment variable ZEEBE_ADDRESS or localhost:26500 and use TLS
worker = ZeebeWorker(secure_connection=True)

# Connect to zeebe cluster in camunda cloud
camunda_cloud_credentials = CamundaCloudCredentials(client_id="<my_client_id>", client_secret="<my_client_secret>",
                                                    cluster_id="<my_cluster_id>")
worker = ZeebeWorker(credentials=camunda_cloud_credentials)

# We can also use decorators on workers. These decorators will happen before all tasks
worker.before(example_logging_task_decorator)
worker.after(example_logging_task_decorator)

# Add task to worker
worker.add_task(task)

if __name__ == "__main__":
    worker.work()
