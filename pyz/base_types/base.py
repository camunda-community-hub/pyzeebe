import grpc

from pyz.grpc_internals.zeebe_pb2_grpc import GatewayStub


class ZeebeBase(object):
    def __init__(self, hostname: str = None, port: int = None, **kwargs):
        hostname = hostname or 'localhost'
        port = port or 26500
        self._channel = grpc.insecure_channel(f'{hostname}:{port}')
        self.connected = False
        self.retrying_connection = True
        self._channel.subscribe(self.__check_connectivity, try_to_connect=True)
        self.zeebe_client = GatewayStub(self._channel)

    def __check_connectivity(self, value: str):
        if value == grpc.ChannelConnectivity.READY:
            self.connected = True
        elif value != grpc.ChannelConnectivity.CONNECTING:
            self.connected = False
            self.retrying_connection = True
        else:
            self.connected = False
