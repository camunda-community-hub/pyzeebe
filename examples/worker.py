from typing import Dict

from pyzeebe import Task, TaskContext, TaskStatusController, ZeebeWorker, CamundaCloudCredentials


def example_task() -> Dict:
    print('Working on job')
    return {'output': f'Hello world, test!'}


def example_exception_handler(exc: Exception, context: TaskContext, controller: TaskStatusController) -> None:
    print(exc)
    print(context)
    controller.error(f'Failed to run task {context.type}. Reason: {exc}')


task = Task(task_type='test', task_handler=example_task, exception_handler=example_exception_handler)

# Will use environment variable ZEEBE_ADDRESS or localhost:26500 and NOT use TLS
worker = ZeebeWorker()

# Will use environment variable ZEEBE_ADDRESS or localhost:26500 and use TLS
worker = ZeebeWorker(secure_connection=True)

# Connect to zeebe cluster in camunda cloud
camunda_cloud_credentials = CamundaCloudCredentials(client_id='<my_client_id>', client_secret='<my_client_secret>',
                                                    cluster_id='<my_cluster_id>')
worker = ZeebeWorker(credentials=camunda_cloud_credentials)

worker.add_task(task)

if __name__ == '__main__':
    worker.work()
