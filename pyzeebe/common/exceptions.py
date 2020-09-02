class TaskNotFound(Exception):
    pass


class WorkflowDoesNotExist(Exception):
    def __init__(self, bpmn_process_id: str, version: int):
        super().__init__(
            f'Workflow definition: {bpmn_process_id}  with {version} does not exist. Have you forgotten to deploy it?')
        self.bpmn_process_id = bpmn_process_id
        self.version = version
