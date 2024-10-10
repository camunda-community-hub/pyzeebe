from .process_run import ProcessRun


class ProcessStats:
    def __init__(self, process_name: str):
        self.process_name = process_name
        self.runs: list[ProcessRun] = []

    def add_process_run(self, process: ProcessRun):
        self.runs.append(process)

    def has_process_been_run(self, process_instance_key: int) -> bool:
        return any(run.instance_key == process_instance_key for run in self.runs if run.instance_key)

    def has_process_with_variables_been_run(self, variables: dict) -> bool:
        return any(run.variables == variables for run in self.runs)

    def get_process_runs(self) -> int:
        return len(self.runs)
