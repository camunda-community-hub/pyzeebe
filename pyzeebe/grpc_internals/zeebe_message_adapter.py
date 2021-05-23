import json
from typing import Dict

import grpc
from zeebe_grpc.gateway_pb2 import (PublishMessageRequest,
                                    PublishMessageResponse)

from pyzeebe.errors import MessageAlreadyExistsError
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase


class ZeebeMessageAdapter(ZeebeAdapterBase):
    async def publish_message(self, name: str, correlation_key: str, time_to_live_in_milliseconds: int,
                              variables: Dict, message_id: str = None) -> PublishMessageResponse:
        try:
            return await self._gateway_stub.PublishMessage(
                PublishMessageRequest(name=name, correlationKey=correlation_key, messageId=message_id,
                                      timeToLive=time_to_live_in_milliseconds, variables=json.dumps(variables)))
        except grpc.aio.AioRpcError as rpc_error:
            if self.is_error_status(rpc_error, grpc.StatusCode.ALREADY_EXISTS):
                raise MessageAlreadyExistsError()
            else:
                await self._common_zeebe_grpc_errors(rpc_error)
