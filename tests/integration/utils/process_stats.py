from typing import Dict, List


class ProcessStats:
    def __init__(self, process_name: str):
        self.process_name = process_name
        self.runs: List[Dict] = []

    def add_process_run(self, starting_parameters: Dict):
        self.runs.append({"starting_parameters": starting_parameters})

    def get_process_runs(self) -> int:
        return len(self.runs)
