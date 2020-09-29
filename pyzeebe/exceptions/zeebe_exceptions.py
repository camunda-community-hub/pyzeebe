from pyzeebe.exceptions.pyzeebe_exceptions import PyZeebeException


class ZeebeBackPressure(PyZeebeException):
    pass


class ZeebeGatewayUnavailable(PyZeebeException):
    pass


class ZeebeInternalError(PyZeebeException):
    pass
