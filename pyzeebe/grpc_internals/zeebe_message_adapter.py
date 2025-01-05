from __future__ import annotations

import json

import grpc

from pyzeebe.errors import MessageAlreadyExistsError
from pyzeebe.grpc_internals.grpc_utils import is_error_status
from pyzeebe.grpc_internals.zeebe_adapter_base import ZeebeAdapterBase
from pyzeebe.proto.gateway_pb2 import BroadcastSignalRequest, PublishMessageRequest
from pyzeebe.types import Variables

from .types import BroadcastSignalResponse, PublishMessageResponse


class ZeebeMessageAdapter(ZeebeAdapterBase):
    async def broadcast_signal(
        self,
        signal_name: str,
        variables: Variables,
        tenant_id: str | None = None,
    ) -> BroadcastSignalResponse:
        try:
            response = await self._gateway_stub.BroadcastSignal(
                BroadcastSignalRequest(
                    signalName=signal_name,
                    variables=json.dumps(variables),
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            await self._handle_grpc_error(grpc_error)

        return BroadcastSignalResponse(key=response.key, tenant_id=response.tenantId)

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
                    messageId=message_id,  # type: ignore[arg-type]
                    timeToLive=time_to_live_in_milliseconds,
                    variables=json.dumps(variables),
                    tenantId=tenant_id,  # type: ignore[arg-type]
                )
            )
        except grpc.aio.AioRpcError as grpc_error:
            if is_error_status(grpc_error, grpc.StatusCode.ALREADY_EXISTS):
                raise MessageAlreadyExistsError() from grpc_error
            await self._handle_grpc_error(grpc_error)

        return PublishMessageResponse(key=response.key, tenant_id=response.tenantId)
