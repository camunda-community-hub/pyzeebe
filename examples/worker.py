import asyncio

from pyzeebe import (
    Job,
    ZeebeWorker,
    create_camunda_cloud_channel,
    create_insecure_channel,
    create_secure_channel,
)
from pyzeebe.errors import BusinessError
from pyzeebe.job.job import JobController


# Use decorators to add functionality before and after tasks. These will not fail the task
async def example_logging_task_decorator(job: Job) -> Job:
    print(job)
    return job


# Will use environment variable ZEEBE_ADDRESS or localhost:26500 and NOT use TLS
# create_insecure_channel returns a grpc.aio.Channel instance. If needed you
# can build one on your own
grpc_channel = create_insecure_channel()
worker = ZeebeWorker(grpc_channel)

# With custom grpc_address
grpc_channel = create_insecure_channel(grpc_address="zeebe-gateway.mydomain:443")
worker = ZeebeWorker(grpc_channel)

# Will use environment variable ZEEBE_ADDRESS or localhost:26500 and use TLS
grpc_channel = create_secure_channel()
worker = ZeebeWorker(grpc_channel)

# With custom grpc_address
grpc_channel = create_secure_channel(grpc_address="zeebe-gateway.mydomain:443")
worker = ZeebeWorker(grpc_channel)

# Connect to zeebe cluster in camunda cloud
grpc_channel = create_camunda_cloud_channel(
    client_id="<my_client_id>",
    client_secret="<my_client_secret>",
    cluster_id="<my_cluster_id>",
    region="<region>",  # Default value is bru-2
)
worker = ZeebeWorker(grpc_channel)

# Decorators allow us to add functionality before and after each job
worker.before(example_logging_task_decorator)
worker.after(example_logging_task_decorator)


# Create a task like this:
@worker.task(task_type="test")
def example_task() -> dict:
    return {"output": "Hello world, test!"}


# Or like this:
@worker.task(task_type="test2")
async def second_example_task() -> dict:
    return {"output": "Hello world, test2!"}


# Create a task that will return a single value (not a dict) like this:
# This task will return to zeebe: { y: x + 1 }
@worker.task(task_type="add_one", single_value=True, variable_name="y")
async def add_one(x: int) -> int:
    return x + 1


# The default exception handler will call job_controller.set_error_status
# on raised BusinessError, and propagate its error_code
# so the specific business error can be caught in the Zeebe process
@worker.task(task_type="business_exception_task")
def exception_task():
    raise BusinessError("invalid-credit-card")


# Define a custom exception_handler for a task like so:
async def example_exception_handler(exception: Exception, job: Job, job_controller: JobController) -> None:
    print(exception)
    print(job)
    await job_controller.set_failure_status(f"Failed to run task {job.type}. Reason: {exception}")


@worker.task(task_type="exception_task", exception_handler=example_exception_handler)
async def exception_task():
    raise Exception("Oh no!")


# We can also add decorators to tasks.
# The order of the decorators will be as follows:
# Worker decorators -> Task decorators -> Task -> Task decorators -> Worker decorators
# Here is how:
@worker.task(
    task_type="decorator_task",
    before=[example_logging_task_decorator],
    after=[example_logging_task_decorator],
)
async def decorator_task() -> dict:
    return {"output": "Hello world, test!"}


if __name__ == "__main__":
    loop = asyncio.get_running_loop()
    loop.run_until_complete(worker.work())
