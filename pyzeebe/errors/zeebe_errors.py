import grpc

from pyzeebe.errors.pyzeebe_errors import PyZeebeError


class ZeebeBackPressureError(PyZeebeError):
    """If Zeebe is currently in back pressure (too many requests)

    See: https://docs.camunda.io/docs/self-managed/zeebe-deployment/operations/backpressure/
    """


class ZeebeGatewayUnavailableError(PyZeebeError):
    pass


class ZeebeInternalError(PyZeebeError):
    pass


class ZeebeDeadlineExceeded(PyZeebeError):
    """If Zeebe hasn't responded after a certain timeout

    See: https://grpc.io/docs/guides/deadlines/
    """


class UnknownGrpcStatusCodeError(PyZeebeError):
    def __init__(self, grpc_error: grpc.aio.AioRpcError):
        super().__init__()
        self.grpc_error = grpc_error
