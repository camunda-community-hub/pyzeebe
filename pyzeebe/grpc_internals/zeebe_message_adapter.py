from __future__ import annotations

import json

import grpc
from zeebe_grpc.gateway_pb2 import PublishMessageRequest

from pyzeebe.errors import MessageAlreadyExistsError
from pyzeebe.grpc_internals.grpc_utils import is_error_status
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.types import Variables

from .types import PublishMessageResponse


class ZeebeMessageAdapter(ZeebeAdapterBase):
    async def publish_message(
        self,
        name: str,
        correlation_key: str,
        time_to_live_in_milliseconds: int,
        variables: Variables,
        message_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PublishMessageResponse:
        try:
            response = await self._gateway_stub.PublishMessage(
                PublishMessageRequest(
                    name=name,
                    correlationKey=correlation_key,
                    messageId=message_id,
                    timeToLive=time_to_live_in_milliseconds,
                    variables=json.dumps(variables),
                    tenantId=tenant_id,
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.ALREADY_EXISTS):
                raise MessageAlreadyExistsError() from grpc_error
            await self._handle_grpc_error(grpc_error)

        return PublishMessageResponse(key=response.key, tenant_id=response.tenantId)
