import logging
import os

import grpc
from zeebe_grpc.gateway_pb2_grpc import GatewayStub

from pyzeebe.credentials.base_credentials import BaseCredentials
from pyzeebe.exceptions import ZeebeBackPressure, ZeebeGatewayUnavailable, ZeebeInternalError

logger = logging.getLogger(__name__)


class ZeebeAdapterBase(object):
    def __init__(self, hostname: str = None, port: int = None, credentials: BaseCredentials = None,
                 channel: grpc.Channel = None, secure_connection: bool = False):
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
            return grpc.secure_channel(connection_uri, credentials.grpc_credentials)
        elif secure_connection:
            return grpc.secure_channel(connection_uri, grpc.ssl_channel_credentials())
        else:
            return grpc.insecure_channel(connection_uri)

    def _check_connectivity(self, value: grpc.ChannelConnectivity) -> None:
        logger.debug(f"Grpc channel connectivity changed to: {value}")
        if value in [grpc.ChannelConnectivity.READY, grpc.ChannelConnectivity.IDLE]:
            logger.debug(f"Connected to {self.connection_uri or 'zeebe'}")
            self.connected = True
            self.retrying_connection = False
        elif value == grpc.ChannelConnectivity.CONNECTING:
            logger.debug(f"Connecting to {self.connection_uri or 'zeebe'}.")
            self.connected = False
            self.retrying_connection = True
        elif value == grpc.ChannelConnectivity.TRANSIENT_FAILURE:
            logger.warning(f"Lost connection to {self.connection_uri or 'zeebe'}. Retrying...")
            self.connected = False
            self.retrying_connection = True
        elif value == grpc.ChannelConnectivity.SHUTDOWN:
            logger.error(f"Failed to establish connection to {self.connection_uri or 'zeebe'}. Non recoverable")
            self.connected = False
            self.retrying_connection = False
            raise ConnectionAbortedError(f"Lost connection to {self.connection_uri or 'zeebe'}")

    def _common_zeebe_grpc_errors(self, rpc_error: grpc.RpcError):
        if self.is_error_status(rpc_error, grpc.StatusCode.RESOURCE_EXHAUSTED):
            raise ZeebeBackPressure()
        elif self.is_error_status(rpc_error, grpc.StatusCode.UNAVAILABLE):
            raise ZeebeGatewayUnavailable()
        elif self.is_error_status(rpc_error, grpc.StatusCode.INTERNAL):
            raise ZeebeInternalError()
        else:
            raise rpc_error

    @staticmethod
    def is_error_status(rpc_error: grpc.RpcError, status_code: grpc.StatusCode):
        return rpc_error._state.code == status_code
