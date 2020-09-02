[![Coverage Status](https://coveralls.io/repos/github/JonatanMartens/pyzeebe/badge.svg?branch=master)](https://coveralls.io/github/JonatanMartens/pyzeebe?branch=master)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/JonatanMartens/pyzeebe/Test%20pyzeebe/master)
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
| 1.0.1           | 0.24.2         |

## Getting Started
To install:

`pip install pyzeebe`

## Usage

### Worker

```python
from pyzeebe import ZeebeWorker, Task, TaskStatusController, TaskContext

def example_task(input: str):
    return {'output': f'Hello world, {input}!'}

def on_error(exception: Exception, context: TaskContext, task_status_controller: TaskStatusController):
    """
    on_error will be called when the task fails
    """ 
    print(exception)
    task_status_controller.error(f'Failed to handle task {context.type}. Error: {str(exception)}')

task = Task(type='example', task_handler=example_task, exception_handler=on_error) # Create task object from example_task

worker = ZeebeWorker(hostname='<zeebe_host>', port=26500) # Create a zeebe worker
worker.add_task(task) # Add task to zeebe worker

worker.work() # Now every time that a task with type example is called example_task will be called
```

### Client

```python
from pyzeebe import ZeebeClient

# Create a zeebe client
zeebe_client = ZeebeClient(hostname='localhost', port=26500)

# Run a workflow
workflow_instance_key = zeebe_client.run_workflow(bpmn_process_id='My zeebe workflow', variables={})

# Run a workflow and receive the result
workflow_result = zeebe_client.run_workflow_with_result(bpmn_process_id='My zeebe workflow',
                                                        timeout=10000)  # Will wait 10000 milliseconds (10 seconds)

# Deploy a bpmn workflow definition
zeebe_client.deploy_workflow('workflow.bpmn')

# Cancel a running workflow
zeebe_client.cancel_workflow_instance(workflow_instance_key=12345)

# Publish message
zeebe_client.publish_message(name='message_name', correlation_key='some_id')


```

## Tests
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install pyzeebe
 
`pytest .`

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


## Versioning
We use [SemVer](semver.org) for versioning. For the versions available, see the tags on this repository.

## License
We use the MIT license, see [LICENSE.md](LICENSE.md) for details