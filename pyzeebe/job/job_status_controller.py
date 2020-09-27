from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter
from pyzeebe.job.job import Job


class JobStatusController(object):
    def __init__(self, job: Job, zeebe_adapter: ZeebeAdapter):
        self.zeebe_adapter = zeebe_adapter
        self.job = job

    def success(self) -> None:
        self.zeebe_adapter.complete_job(job_key=self.job.key, variables=self.job.variables)

    def failure(self, message: str) -> None:
        self.zeebe_adapter.fail_job(job_key=self.job.key, message=message)

    def error(self, message: str):
        self.zeebe_adapter.throw_error(job_key=self.job.key, message=message)
