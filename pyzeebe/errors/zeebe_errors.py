import grpc

from pyzeebe.errors.pyzeebe_errors import PyZeebeError


class ZeebeBackPressureError(PyZeebeError):
    pass


class ZeebeGatewayUnavailableError(PyZeebeError):
    pass


class ZeebeInternalError(PyZeebeError):
    pass


class UnkownGrpcStatusCodeError(PyZeebeError):
    def __init__(self, grpc_error: grpc.aio.AioRpcError):
        super().__init__()
        self.grpc_error = grpc_error
