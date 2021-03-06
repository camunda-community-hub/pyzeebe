from pyzeebe.errors.pyzeebe_errors import PyZeebeError


class ZeebeBackPressureError(PyZeebeError):
    pass


class ZeebeGatewayUnavailableError(PyZeebeError):
    pass


class ZeebeInternalError(PyZeebeError):
    pass
