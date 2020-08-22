[![Coverage Status](https://coveralls.io/repos/github/JonatanMartens/zeebepy/badge.svg?branch=master)](https://coveralls.io/github/JonatanMartens/zeebepy?branch=master)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/JonatanMartens/zeebepy/Zeebepy)
![GitHub issues](https://img.shields.io/github/issues-raw/JonatanMartens/zeebepy)
![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/JonatanMartens/zeebepy)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/JonatanMartens/zeebepy)
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/JonatanMartens/zeebepy)
![PyPI - Downloads](https://img.shields.io/pypi/dm/zeebepy)
![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/JonatanMartens/zeebepy)
![PyPI](https://img.shields.io/pypi/v/zeebepy)



# Zeebepy
Zeebepy is a python grpc client for Zeebe.

Zeebe version support:

| Zeebepy version | Tested Zeebe versions |
|:---------------:|----------------|
| 0.0.1           | 0.24.2         |

## Getting Started
To install:

`pip install zeebepy`

## Usage

### Worker

```python
from zeebepy import ZeebeWorker, Task, TaskStatusController, JobContext

def example_task(input: str):
    return {'output': f'Hello world, {input}!'}

def on_error(exception: Exception, context: JobContext, task_status_controller: TaskStatusController):
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

## Tests
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install zeebepy
 
`pytest .`

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


## Versioning
We use [SemVer](semver.org) for versioning. For the versions available, see the tags on this repository.

## License
We use the MIT license, see [LICENSE.md](LICENSE.md) for details