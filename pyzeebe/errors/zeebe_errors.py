import grpc

from pyzeebe.errors.pyzeebe_errors import PyZeebeError


class ZeebeBackPressureError(PyZeebeError):
    pass


class ZeebeGatewayUnavailableError(PyZeebeError):
    pass


class ZeebeInternalError(PyZeebeError):
    pass


class UnkownRpcStatusCodeError(PyZeebeError):
    def __init__(self, rpc_error: grpc.aio.AioRpcError):
        super().__init__()
        self.rpc_error = rpc_error
