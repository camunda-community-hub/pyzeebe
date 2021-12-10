import json
from typing import Dict

import grpc
from zeebe_grpc.gateway_pb2 import PublishMessageRequest, PublishMessageResponse

from pyzeebe.errors import MessageAlreadyExistsError
from pyzeebe.grpc_internals.grpc_utils import is_error_status
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase


class ZeebeMessageAdapter(ZeebeAdapterBase):
    async def publish_message(
        self,
        name: str,
        correlation_key: str,
        time_to_live_in_milliseconds: int,
        variables: Dict,
        message_id: str = None,
    ) -> PublishMessageResponse:
        try:
            return await self._gateway_stub.PublishMessage(
                PublishMessageRequest(
                    name=name,
                    correlationKey=correlation_key,
                    messageId=message_id,
                    timeToLive=time_to_live_in_milliseconds,
                    variables=json.dumps(variables),
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.ALREADY_EXISTS):
                raise MessageAlreadyExistsError() from grpc_error
            await self._handle_grpc_error(grpc_error)
