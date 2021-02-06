import grpc


class GRPCStatusCode:
    def __init__(self, code: grpc.StatusCode):
        self.code = code
