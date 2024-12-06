import grpc

from pyzeebe.errors.pyzeebe_errors import PyZeebeError


class ZeebeError(PyZeebeError):
    """Base exception for all Zeebe errors."""

    def __init__(self, grpc_error: grpc.aio.AioRpcError):
        super().__init__()
        self.grpc_error = grpc_error

    def __str__(self) -> str:
        return "{}(grpc_error={}(code={}, details={}, debug_error_string={}))".format(
            self.__class__.__qualname__,
            self.grpc_error.__class__.__qualname__,
            self.grpc_error._code,
            self.grpc_error._details,
            self.grpc_error._debug_error_string,
        )

    def __repr__(self) -> str:
        return self.__str__()


class ZeebeBackPressureError(ZeebeError):
    """If Zeebe is currently in back pressure (too many requests)

    See: https://docs.camunda.io/docs/self-managed/zeebe-deployment/operations/backpressure/
    """


class ZeebeGatewayUnavailableError(ZeebeError):
    pass


class ZeebeInternalError(ZeebeError):
    pass


class ZeebeDeadlineExceeded(ZeebeError):
    """If Zeebe hasn't responded after a certain timeout

    See: https://grpc.io/docs/guides/deadlines/
    """


class UnknownGrpcStatusCodeError(ZeebeError):
    pass
