import asyncio
from typing import Any, Dict, List, Optional, Tuple

import grpc
from typing_extensions import deprecated

from pyzeebe import ZeebeClient
from pyzeebe.types import Variables


class SyncZeebeClient:
    def __init__(self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = 10) -> None:
        self.loop = asyncio.get_event_loop()
        self.client = ZeebeClient(grpc_channel, max_connection_retries)

    def run_process(
        self,
        bpmn_process_id: str,
        variables: Optional[Variables] = None,
        version: int = -1,
        tenant_id: Optional[str] = None,
    ) -> int:
        return self.loop.run_until_complete(self.client.run_process(bpmn_process_id, variables, version, tenant_id))

    def run_process_with_result(
        self,
        bpmn_process_id: str,
        variables: Optional[Variables] = None,
        version: int = -1,
        timeout: int = 0,
        variables_to_fetch: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        return self.loop.run_until_complete(
            self.client.run_process_with_result(
                bpmn_process_id, variables, version, timeout, variables_to_fetch, tenant_id
            )
        )

    def cancel_process_instance(self, process_instance_key: int) -> int:
        return self.loop.run_until_complete(self.client.cancel_process_instance(process_instance_key))

    @deprecated("Deprecated since Zeebe 8.0. Use deploy_resource instead")
    def deploy_process(self, *process_file_path: str) -> None:
        return self.loop.run_until_complete(self.client.deploy_process(*process_file_path))

    def deploy_resource(self, *resource_file_path: str, tenant_id: Optional[str] = None) -> None:
        return self.loop.run_until_complete(self.client.deploy_resource(*resource_file_path, tenant_id=tenant_id))

    def publish_message(
        self,
        name: str,
        correlation_key: str,
        variables: Optional[Variables] = None,
        time_to_live_in_milliseconds: int = 60000,
        message_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> None:
        return self.loop.run_until_complete(
            self.client.publish_message(
                name,
                correlation_key,
                variables,
                time_to_live_in_milliseconds,
                message_id,
                tenant_id,
            )
        )
