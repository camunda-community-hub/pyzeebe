[![](https://img.shields.io/badge/Community%20Extension-An%20open%20source%20community%20maintained%20project-FF4700)](https://github.com/camunda-community-hub/community)
[![](https://img.shields.io/badge/Lifecycle-Stable-brightgreen)](https://github.com/Camunda-Community-Hub/community/blob/main/extension-lifecycle.md#stable-)
![Compatible with: Camunda Platform 8](https://img.shields.io/badge/Compatible%20with-Camunda%20Platform%208-0072Ce)

[![Coverage Status](https://coveralls.io/repos/github/JonatanMartens/pyzeebe/badge.svg?branch=master)](https://coveralls.io/github/JonatanMartens/pyzeebe?branch=master)
![Test pyzeebe](https://github.com/camunda-community-hub/pyzeebe/workflows/Test%20pyzeebe/badge.svg)
![Integration test pyzeebe](https://github.com/camunda-community-hub/pyzeebe/workflows/Integration%20test%20pyzeebe/badge.svg)

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/camunda-community-hub/pyzeebe)
![PyPI](https://img.shields.io/pypi/v/pyzeebe)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyzeebe)


# Pyzeebe

pyzeebe is a python grpc client for Zeebe.

Zeebe version support:

| Pyzeebe version | Tested Zeebe versions  |
| :-------------: | ---------------------- |
|      4.x.x      | 8.5, 8.6, 8.7          |
|      3.x.x      | 1.0.0                  |
|      2.x.x      | 0.23, 0.24, 0.25, 0.26 |
|      1.x.x      | 0.23, 0.24             |

## Getting Started

To install:

`pip install pyzeebe`

For full documentation please visit: https://camunda-community-hub.github.io/pyzeebe/

## Usage

### Worker

The `ZeebeWorker` class gets jobs from the gateway and runs them.

```python
import asyncio

from pyzeebe import ZeebeWorker, Job, JobController, create_insecure_channel


channel = create_insecure_channel(grpc_address="localhost:26500") # Create grpc channel
worker = ZeebeWorker(channel) # Create a zeebe worker


async def on_error(exception: Exception, job: Job, job_controller: JobController):
    """
    on_error will be called when the task fails
    """
    print(exception)
    await job_controller.set_error_status(job, f"Failed to handle job {job}. Error: {str(exception)}")


@worker.task(task_type="example", exception_handler=on_error)
def example_task(input: str) -> dict:
    return {"output": f"Hello world, {input}!"}


@worker.task(task_type="example2", exception_handler=on_error)
async def another_example_task(name: str) -> dict: # Tasks can also be async
    return {"output": f"Hello world, {name} from async task!"}

loop = asyncio.get_running_loop()
loop.run_until_complete(worker.work()) # Now every time that a task with type `example` or `example2` is called, the corresponding function will be called
```

Stop a worker:

```python
await zeebe_worker.stop() # Stops worker after all running jobs have been completed
```

### Client

```python
from pyzeebe import ZeebeClient, create_insecure_channel

# Create a zeebe client
channel = create_insecure_channel(grpc_address="localhost:26500")
zeebe_client = ZeebeClient(channel)

# Run a Zeebe process instance
process_instance_key = await zeebe_client.run_process(bpmn_process_id="My zeebe process", variables={})

# Run a process and receive the result
process_instance_key, process_result = await zeebe_client.run_process_with_result(
    bpmn_process_id="My zeebe process",
    timeout=10000
)

# Deploy a BPMN process definition
await zeebe_client.deploy_resource("process.bpmn")

# Cancel a running process
await zeebe_client.cancel_process_instance(process_instance_key=12345)

# Publish message
await zeebe_client.publish_message(name="message_name", correlation_key="some_id")

```

## Tests

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install pyzeebe

`pytest tests/unit`

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Versioning

We use [SemVer](semver.org) for versioning. For the versions available, see the tags on this repository.

## License

We use the MIT license, see [LICENSE.md](LICENSE.md) for details
