[![Coverage Status](https://coveralls.io/repos/github/JonatanMartens/pyzeebe/badge.svg?branch=master)](https://coveralls.io/github/JonatanMartens/pyzeebe?branch=master)
![Test pyzeebe](https://github.com/JonatanMartens/pyzeebe/workflows/Test%20pyzeebe/badge.svg)
![Integration test pyzeebe](https://github.com/JonatanMartens/pyzeebe/workflows/Integration%20test%20pyzeebe/badge.svg)
![GitHub issues](https://img.shields.io/github/issues-raw/JonatanMartens/pyzeebe)
![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/JonatanMartens/pyzeebe)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/JonatanMartens/pyzeebe)
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/JonatanMartens/pyzeebe)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyzeebe)
![PyPI](https://img.shields.io/pypi/v/pyzeebe)



# Pyzeebe
pyzeebe is a python grpc client for Zeebe.

Zeebe version support:

| Pyzeebe version | Tested Zeebe versions |
|:---------------:|----------------|
| 2.x.x           | 0.23, 0.24, 0.25         |
| 1.x.x           | 0.23, 0.24         |

## Getting Started
To install:

`pip install pyzeebe`

For full documentation please visit: https://pyzeebe.readthedocs.io/en/stable/

## Usage

### Worker

The `ZeebeWorker` class uses threading to get and run jobs.

```python
from pyzeebe import ZeebeWorker, Job


def on_error(exception: Exception, job: Job):
    """
    on_error will be called when the task fails
    """ 
    print(exception)
    job.set_error_status(f"Failed to handle job {job}. Error: {str(exception)}")



worker = ZeebeWorker(hostname="<zeebe_host>", port=26500) # Create a zeebe worker

@worker.task(task_type="example", exception_handler=on_error)
def example_task(input: str):
    return {"output": f"Hello world, {input}!"}


worker.work() # Now every time that a task with type example is called example_task will be called
```

Stop a worker:
```python
zeebe_worker.work() # Worker will begin working
zeebe_worker.stop() # Stops worker after all running jobs have been completed 
```

### Client

```python
from pyzeebe import ZeebeClient

# Create a zeebe client
zeebe_client = ZeebeClient(hostname="localhost", port=26500)

# Run a workflow
workflow_instance_key = zeebe_client.run_workflow(bpmn_process_id="My zeebe workflow", variables={})

# Run a workflow and receive the result
workflow_result = zeebe_client.run_workflow_with_result(bpmn_process_id="My zeebe workflow",
                                                        timeout=10000)  # Will wait 10000 milliseconds (10 seconds)

# Deploy a bpmn workflow definition
zeebe_client.deploy_workflow("workflow.bpmn")

# Cancel a running workflow
zeebe_client.cancel_workflow_instance(workflow_instance_key=12345)

# Publish message
zeebe_client.publish_message(name="message_name", correlation_key="some_id")

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