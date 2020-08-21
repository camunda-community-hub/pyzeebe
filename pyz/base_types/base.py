import grpc

from pyz.grpc_internals.zeebe_pb2_grpc import GatewayStub


class ZeebeBase(object):
    def __init__(self, hostname: str = None, port: int = None, **kwargs):
        print('Called zeebe base')
        hostname = hostname or 'localhost'
        port = port or 26500
        self._channel = grpc.insecure_channel(f'{hostname}:{port}')
        self.zeebe_client = GatewayStub(self._channel)
