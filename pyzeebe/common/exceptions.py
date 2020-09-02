class TaskNotFound(Exception):
    pass


class WorkflowNotFound(Exception):
    def __init__(self, bpmn_process_id: str, version: int):
        super().__init__(
            f'Workflow definition: {bpmn_process_id}  with {version} was not found')
        self.bpmn_process_id = bpmn_process_id
        self.version = version


class WorkflowInstanceNotFound(Exception):
    def __init__(self, workflow_instance_key: int):
        super().__init__(f'Workflow instance key: {workflow_instance_key} was not found')
        self.workflow_instance_key = workflow_instance_key


class WorkflowHasNoStartEvent(Exception):
    def __init__(self, bpmn_process_id: str):
        super().__init__(f"Workflow {bpmn_process_id} has no start event that can be called manually")
        self.bpmn_process_id = bpmn_process_id


class ActivateJobsRequestInvalid(Exception):
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


class JobAlreadyDeactivated(Exception):
    def __init__(self, job_key: int):
        super().__init__(f"Job {job_key} was already stopped (Completed/Failed/Error)")
        self.job_key = job_key


class JobNotFound(Exception):
    def __init__(self, job_key: int):
        super().__init__(f"Job {job_key} not found")
        self.job_key = job_key


class WorkflowInvalid(Exception):
    pass


class MessageAlreadyExists(Exception):
    pass


class ElementNotFound(Exception):
    pass


class InvalidJSON(Exception):
    pass


class ZeebeBackPressure(Exception):
    pass


class ZeebeGatewayUnavailable(Exception):
    pass


class ZeebeInternalError(Exception):
    pass
