from typing import Dict, List

import grpc

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter


class ZeebeClient(object):
    def __init__(self, hostname: str = None, port: int = None, channel: grpc.Channel = None):
        self.zeebe_adapter = ZeebeAdapter(hostname=hostname, port=port, channel=channel)

    def run_workflow(self, bpmn_process_id: str, variables: Dict = None, version: int = -1) -> int:
        return self.zeebe_adapter.create_workflow_instance(bpmn_process_id=bpmn_process_id, variables=variables or {},
                                                           version=version)

    def run_workflow_with_result(self, bpmn_process_id: str, variables: Dict = None, version: int = -1,
                                 timeout: int = 0, variables_to_fetch: List[str] = None) -> Dict:
        return self.zeebe_adapter.create_workflow_instance_with_result(bpmn_process_id=bpmn_process_id,
                                                                       variables=variables or {}, version=version,
                                                                       timeout=timeout,
                                                                       variables_to_fetch=variables_to_fetch or [])

    def cancel_workflow_instance(self, workflow_instance_key: int) -> int:
        self.zeebe_adapter.cancel_workflow_instance(workflow_instance_key=workflow_instance_key)
        return workflow_instance_key

    def deploy_workflow(self, *workflow_file_path: str):
        self.zeebe_adapter.deploy_workflow(*workflow_file_path)

    def publish_message(self, name: str, correlation_key: str, variables: Dict = None,
                        time_to_live_in_milliseconds: int = 60000) -> None:
        self.zeebe_adapter.publish_message(name=name, correlation_key=correlation_key,
                                           time_to_live_in_milliseconds=time_to_live_in_milliseconds,
                                           variables=variables or {})
