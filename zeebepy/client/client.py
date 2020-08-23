from typing import Dict, List

from zeebepy.grpc_internals.zeebe_adapter import ZeebeAdapter


class ZeebeClient(object):
    def __init__(self, hostname: str = None, port: int = None):
        self.zeebe_adapter = ZeebeAdapter(hostname=hostname, port=port)

    def run_workflow(self, bpmn_process_id: str, variables: Dict = None, version: int = -1) -> str:
        return self.zeebe_adapter.create_workflow_instance(bpmn_process_id=bpmn_process_id, variables=variables or {},
                                                           version=version)

    def run_workflow_with_result(self, bpmn_process_id: str, variables: Dict = None, version: int = -1,
                                 timeout: int = 0, variables_to_fetch: List[str] = None) -> Dict:
        return self.zeebe_adapter.create_workflow_instance_with_result(bpmn_process_id=bpmn_process_id,
                                                                       variables=variables or {}, version=version,
                                                                       timeout=timeout,
                                                                       variables_to_fetch=variables_to_fetch or [])
