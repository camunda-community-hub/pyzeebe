from pyzeebe.exceptions.pyzeebe_exceptions import PyZeebeException


class ActivateJobsRequestInvalid(PyZeebeException):
    def __init__(self, task_type: str, worker: str, timeout: int, max_jobs_to_activate: int):
        msg = "Failed to activate jobs. Reasons:"
        if task_type == "" or task_type is None:
            msg = msg + "task_type is empty, "
        if worker == "" or task_type is None:
            msg = msg + "worker is empty, "
        if timeout < 1:
            msg = msg + "job timeout is smaller than 0ms, "
        if max_jobs_to_activate < 1:
            msg = msg + "max_jobs_to_activate is smaller than 0ms, "

        super().__init__(msg)


class JobAlreadyDeactivated(PyZeebeException):
    def __init__(self, job_key: int):
        super().__init__(f"Job {job_key} was already stopped (Completed/Failed/Error)")
        self.job_key = job_key


class JobNotFound(PyZeebeException):
    def __init__(self, job_key: int):
        super().__init__(f"Job {job_key} not found")
        self.job_key = job_key
