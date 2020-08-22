from pyz.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyz.task.task_context import TaskContext


class TaskStatusSetter:
    def __init__(self, context: TaskContext, zeebe_client: ZeebeAdapter):
        self.zeebe_client = zeebe_client
        self.context = context

    def success(self) -> None:
        self.zeebe_client.complete_job(job_key=self.context.key, variables=self.context.variables)

    def failure(self, code: str, message: str) -> None:
        self.zeebe_client.fail_job(job_key=self.context.key, error_code=code, message=message)

    def error(self, code: str, message: str):
        self.zeebe_client.throw_error(job_key=self.context.key, error_code=code, message=message)
