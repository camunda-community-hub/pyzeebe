from typing import Dict


class ProcessRun:
    def __init__(self, instance_key: int, variables: Dict):
        self.instance_key = instance_key
        self.variables = variables
