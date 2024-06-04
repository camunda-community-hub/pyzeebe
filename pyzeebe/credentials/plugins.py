from typing import Optional

import grpc

from pyzeebe.credentials.base import Credentials
from pyzeebe.credentials.typing import AuthMetadata


class AuthMetadataPlugin(grpc.AuthMetadataPlugin):
    def __init__(self, *, credentials: Credentials) -> None:
        super().__init__()
        self._credentials = credentials

    def __call__(self, context: grpc.AuthMetadataContext, callback: grpc.AuthMetadataPluginCallback) -> None:
        try:
            metadata = self._credentials.get_auth_metadata(context)
        except Exception as e:
            self._sign_request(callback, (), e)
        else:
            self._sign_request(callback, metadata, None)

    def _sign_request(
        self, callback: grpc.AuthMetadataPluginCallback, metadata: AuthMetadata, error: Optional[Exception]
    ) -> None:
        callback(metadata, error)
