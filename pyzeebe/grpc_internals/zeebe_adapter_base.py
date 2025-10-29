from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, NoReturn, cast

import grpc
from grpc_health.v1.health_pb2_grpc import HealthStub
from typing_extensions import TypeAlias

from pyzeebe.errors import (
    UnknownGrpcStatusCodeError,
    ZeebeBackPressureError,
    ZeebeDeadlineExceeded,
    ZeebeGatewayUnavailableError,
    ZeebeInternalError,
)
from pyzeebe.errors.pyzeebe_errors import PyZeebeError
from pyzeebe.grpc_internals.grpc_utils import is_error_status
from pyzeebe.proto.gateway_pb2_grpc import GatewayStub

if TYPE_CHECKING:
    from pyzeebe.proto.gateway_pb2_grpc import GatewayAsyncStub

Callback: TypeAlias = Callable[[], None]
logger = logging.getLogger(__name__)


class ZeebeAdapterBase:
    def __init__(self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = -1):
        self._channel = grpc_channel
        self._gateway_stub = cast("GatewayAsyncStub", GatewayStub(grpc_channel))
        self._health_stub = HealthStub(grpc_channel)
        self._connected = True
        self.retrying_connection = False
        self._max_connection_retries = max_connection_retries
        self._current_connection_retries = 0
        self._on_disconnect_callbacks: list[Callback] = []

    @property
    def connected(self) -> bool:
        return self._connected

    def add_disconnect_callback(self, callback: Callback) -> None:
        self._on_disconnect_callbacks.append(callback)

    def _should_retry(self) -> bool:
        return self._max_connection_retries == -1 or self._current_connection_retries < self._max_connection_retries

    async def _handle_grpc_error(self, grpc_error: grpc.aio.AioRpcError) -> NoReturn:
        try:
            pyzeebe_error = self._create_pyzeebe_error_from_grpc_error(grpc_error)
            raise pyzeebe_error
        except (ZeebeGatewayUnavailableError, ZeebeInternalError, ZeebeDeadlineExceeded):
            self._current_connection_retries += 1
            if not self._should_retry():
                await self._close()
            raise

    async def _close(self) -> None:
        try:
            await self._channel.close()
        except Exception as exception:
            logger.exception("Failed to close channel, %s exception was raised", type(exception).__name__)
        finally:
            logger.info(f"Closing grpc channel after {self._max_connection_retries} retries.")
            self._connected = False
            for callback in self._on_disconnect_callbacks:
                callback()

    def _create_pyzeebe_error_from_grpc_error(self, grpc_error: grpc.aio.AioRpcError) -> PyZeebeError:
        if is_error_status(grpc_error, grpc.StatusCode.RESOURCE_EXHAUSTED):
            return ZeebeBackPressureError(grpc_error)
        if is_error_status(grpc_error, grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.CANCELLED):
            return ZeebeGatewayUnavailableError(grpc_error)
        if is_error_status(grpc_error, grpc.StatusCode.INTERNAL):
            return ZeebeInternalError(grpc_error)
        elif is_error_status(grpc_error, grpc.StatusCode.DEADLINE_EXCEEDED):
            return ZeebeDeadlineExceeded(grpc_error)
        return UnknownGrpcStatusCodeError(grpc_error)
