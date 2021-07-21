# type: ignore

import asyncio
from typing import Dict, List, Tuple

import grpc

from pyzeebe import ZeebeClient


class SyncZeebeClient(ZeebeClient):
    def __init__(
        self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = 10
    ):
        super().__init__(grpc_channel, max_connection_retries)
        self.loop = asyncio.get_event_loop()

    def run_process(
        self, bpmn_process_id: str, variables: Dict = None, version: int = -1
    ) -> int:
        return self.loop.run_until_complete(
            super().run_process(bpmn_process_id, variables, version)
        )

    def run_process_with_result(
        self,
        bpmn_process_id: str,
        variables: Dict = None,
        version: int = -1,
        timeout: int = 0,
        variables_to_fetch: List[str] = None,
    ) -> Tuple[int, Dict]:
        return self.loop.run_until_complete(
            super().run_process_with_result(
                bpmn_process_id, variables, version, timeout, variables_to_fetch
            )
        )

    def cancel_process_instance(self, process_instance_key: int) -> int:
        return self.loop.run_until_complete(
            super().cancel_process_instance(process_instance_key)
        )

    def deploy_process(self, *process_file_path: str) -> None:
        return self.loop.run_until_complete(super().deploy_process(*process_file_path))

    def publish_message(
        self,
        name: str,
        correlation_key: str,
        variables: Dict = None,
        time_to_live_in_milliseconds: int = 60000,
        message_id: str = None,
    ) -> None:
        return self.loop.run_until_complete(
            super().publish_message(
                name,
                correlation_key,
                variables,
                time_to_live_in_milliseconds,
                message_id,
            )
        )
