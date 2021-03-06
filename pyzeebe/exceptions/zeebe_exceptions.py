from pyzeebe.exceptions.pyzeebe_exceptions import PyZeebeException


class ZeebeBackPressureError(PyZeebeException):
    pass


class ZeebeGatewayUnavailableError(PyZeebeException):
    pass


class ZeebeInternalError(PyZeebeException):
    pass
