from typing import Dict

from pyzeebe import Job, JobStatusController, ZeebeWorker, CamundaCloudCredentials


def example_exception_handler(exc: Exception, job: Job, controller: JobStatusController) -> None:
    print(exc)
    print(job)
    controller.error(f"Failed to run task {job.type}. Reason: {exc}")


# Use decorators to add functionality before and after tasks. These will not fail the task
def example_logging_task_decorator(job: Job) -> Job:
    print(job)
    return job


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


@worker.task(task_type="test", exception_handler=example_exception_handler,
             before=[example_logging_task_decorator], after=[example_logging_task_decorator])
def example_task() -> Dict:
    return {"output": f"Hello world, test!"}


if __name__ == "__main__":
    worker.work()
