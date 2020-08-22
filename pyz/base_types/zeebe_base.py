import os

import grpc

from pyz.grpc_internals.zeebe_adapter import ZeebeAdapter


class ZeebeBase(object):
    def __init__(self, hostname: str = None, port: int = None, **kwargs):
        self._connection_uri = f'{hostname}:{port}' or os.getenv('ZEEBE_ADDRESS') or 'localhost:26500'
        self._channel = grpc.insecure_channel(self._connection_uri)
        self.connected = False
        self.retrying_connection = True
        self._channel.subscribe(self._check_connectivity, try_to_connect=True)
        self.zeebe_client = ZeebeAdapter(self._channel)

    def _check_connectivity(self, value: grpc.ChannelConnectivity):
        if value in [grpc.ChannelConnectivity.READY, grpc.ChannelConnectivity.IDLE]:
            self.connected = True
            self.retrying_connection = False
        elif value in [grpc.ChannelConnectivity.CONNECTING, grpc.ChannelConnectivity.TRANSIENT_FAILURE]:
            self.connected = False
            self.retrying_connection = True
        elif value == grpc.ChannelConnectivity.SHUTDOWN:
            self.connected = False
            self.retrying_connection = False
            raise ConnectionAbortedError(f'Lost connection to {self._connection_uri}')
