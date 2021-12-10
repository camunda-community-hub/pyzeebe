import logging

import grpc
from zeebe_grpc.gateway_pb2_grpc import GatewayStub

from pyzeebe.errors import (
    ZeebeBackPressureError,
    ZeebeGatewayUnavailableError,
    ZeebeInternalError,
)
from pyzeebe.grpc_internals.grpc_utils import is_error_status

logger = logging.getLogger(__name__)


class ZeebeAdapterBase:
    def __init__(self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = -1):
        self._channel = grpc_channel
        self._gateway_stub = GatewayStub(grpc_channel)
        self.connected = True
        self.retrying_connection = False
        self._max_connection_retries = max_connection_retries
        self._current_connection_retries = 0

    def _should_retry(self):
        return self._max_connection_retries == -1 or self._current_connection_retries < self._max_connection_retries

    async def _common_zeebe_grpc_errors(self, rpc_error: grpc.aio.AioRpcError):
        if is_error_status(rpc_error, grpc.StatusCode.RESOURCE_EXHAUSTED):
            raise ZeebeBackPressureError()
        elif is_error_status(rpc_error, grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.CANCELLED):
            self._current_connection_retries += 1
            if not self._should_retry():
                await self._close()
            raise ZeebeGatewayUnavailableError() from rpc_error
        elif is_error_status(rpc_error, grpc.StatusCode.INTERNAL):
            self._current_connection_retries += 1
            if not self._should_retry():
                await self._close()
            raise ZeebeInternalError() from rpc_error
        else:
            raise rpc_error

    async def _close(self):
        try:
            await self._channel.close()
        except Exception as exception:
            logger.exception(f"Failed to close channel, {type(exception).__name__} exception was raised")
