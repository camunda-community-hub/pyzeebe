import grpc


def is_error_status(rpc_error: grpc.aio.AioRpcError, *status_codes: grpc.StatusCode) -> bool:
    return rpc_error.code() in status_codes
