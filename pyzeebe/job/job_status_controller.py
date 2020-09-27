from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job


class JobStatusController(object):
    def __init__(self, context: Job, zeebe_adapter: ZeebeAdapter):
        self.zeebe_adapter = zeebe_adapter
        self.context = context

    def success(self) -> None:
        self.zeebe_adapter.complete_job(job_key=self.context.key, variables=self.context.variables)

    def failure(self, message: str) -> None:
        self.zeebe_adapter.fail_job(job_key=self.context.key, message=message)

    def error(self, message: str):
        self.zeebe_adapter.throw_error(job_key=self.context.key, message=message)
