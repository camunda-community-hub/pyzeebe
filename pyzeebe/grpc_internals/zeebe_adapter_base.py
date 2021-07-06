import logging
import os

import grpc
from zeebe_grpc.gateway_pb2_grpc import GatewayStub

from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.exceptions import ZeebeBackPressure, ZeebeGatewayUnavailable, ZeebeInternalError
from pyzeebe.grpc_internals.channel_options import get_channel_options

logger = logging.getLogger(__name__)


class ZeebeAdapterBase(object):
    def __init__(self, hostname: str = None, port: int = None, credentials: BaseCredentials = None,
                 channel: grpc.Channel = None, secure_connection: bool = False, max_connection_retries: int = -1):
        if channel:
            self.connection_uri = None
            self._channel = channel
        else:
            self.connection_uri = self._get_connection_uri(hostname, port, credentials)
            self._channel = self._create_channel(self.connection_uri, credentials, secure_connection)

        self.secure_connection = secure_connection
        self.connected = False
        self.retrying_connection = True
        self._channel.subscribe(self._check_connectivity, try_to_connect=True)
        self._gateway_stub = GatewayStub(self._channel)
        self._max_connection_retries = max_connection_retries
        self._current_connection_retries = 0

    @staticmethod
    def _get_connection_uri(hostname: str = None, port: int = None, credentials: BaseCredentials = None) -> str:
        if credentials and credentials.get_connection_uri():
            return credentials.get_connection_uri()
        if hostname or port:
            return f"{hostname or 'localhost'}:{port or 26500}"
        else:
            return os.getenv("ZEEBE_ADDRESS", "localhost:26500")

    @staticmethod
    def _create_channel(connection_uri: str, credentials: BaseCredentials = None,
                        secure_connection: bool = False) -> grpc.Channel:
        if credentials:
            return grpc.secure_channel(connection_uri, credentials.grpc_credentials, options=get_channel_options())
        elif secure_connection:
            return grpc.secure_channel(connection_uri, grpc.ssl_channel_credentials(), options=get_channel_options())
        else:
            return grpc.insecure_channel(connection_uri, options=get_channel_options())

    def _check_connectivity(self, value: grpc.ChannelConnectivity) -> None:
        logger.debug(f"Grpc channel connectivity changed to: {value}")
        self.connected = False

        if value in [grpc.ChannelConnectivity.READY, grpc.ChannelConnectivity.IDLE]:
            logger.debug(f"Connected to {self.connection_uri or 'zeebe'}")
            self.connected = True
            self.retrying_connection = False
            self._current_connection_retries = 0

        elif value == grpc.ChannelConnectivity.CONNECTING:
            logger.debug(f"Connecting to {self.connection_uri or 'zeebe'}.")
            self.retrying_connection = True

        elif value == grpc.ChannelConnectivity.TRANSIENT_FAILURE:
            if self._should_retry():
                logger.warning(f"Lost connection to {self.connection_uri or 'zeebe'}. Retrying...")
                self.retrying_connection = True
                self._current_connection_retries = self._current_connection_retries + 1
            else:
                logger.error(f"Failed to establish connection to {self.connection_uri or 'zeebe'}. Not recoverable")
                self._close()
                self.retrying_connection = False
                raise ConnectionAbortedError(f"Lost connection to {self.connection_uri or 'zeebe'}")

        elif value == grpc.ChannelConnectivity.SHUTDOWN:
            logger.warning(f"Shutting down grpc channel to {self.connection_uri or 'zeebe'}")
            self.retrying_connection = False

    def _should_retry(self):
        return self._max_connection_retries == -1 or self._current_connection_retries < self._max_connection_retries

    def _common_zeebe_grpc_errors(self, rpc_error: grpc.RpcError):
        if self.is_error_status(rpc_error, grpc.StatusCode.RESOURCE_EXHAUSTED):
            raise ZeebeBackPressure()
        elif self.is_error_status(rpc_error, grpc.StatusCode.UNAVAILABLE):
            self._current_connection_retries += 1
            if not self._should_retry():
                self._close()
            raise ZeebeGatewayUnavailable()
        elif self.is_error_status(rpc_error, grpc.StatusCode.INTERNAL):
            self._current_connection_retries += 1
            if not self._should_retry():
                self._close()
            raise ZeebeInternalError()
        else:
            raise rpc_error

    @staticmethod
    def is_error_status(rpc_error: grpc.RpcError, status_code: grpc.StatusCode):
        return rpc_error._state.code == status_code

    def _close(self):
        try:
            self._channel.close()
        except Exception as e:
            logger.exception(f"Failed to close channel, {type(e).__name__} exception was raised")
