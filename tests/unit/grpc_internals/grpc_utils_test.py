import grpc

from pyzeebe.grpc_internals import grpc_utils


class TestIsErrorStatus:
    error = grpc.aio.AioRpcError(grpc.StatusCode.OK, None, None)
    matching_status_code = grpc.StatusCode.OK
    unmatching_status_code = grpc.StatusCode.UNKNOWN

    def test_with_matching_code_returns_true(self):
        assert grpc_utils.is_error_status(self.error, self.matching_status_code)

    def test_with_no_matching_code_returns_false(self):
        assert not grpc_utils.is_error_status(self.error, self.unmatching_status_code)

    def test_with_matching_and_unmatching_code_returns_true(self):
        assert grpc_utils.is_error_status(self.error, self.matching_status_code, self.unmatching_status_code)
