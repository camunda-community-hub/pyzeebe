from typing import Optional

import grpc

from pyzeebe.credentials.base import CredentialsABC
from pyzeebe.credentials.typing import AuthMetadata


class AuthMetadataPlugin(grpc.AuthMetadataPlugin):
    """TODO.

    Args:
        credentials (CredentialsABC): TODO
    """

    def __init__(self, *, credentials: CredentialsABC) -> None:
        self._credentials = credentials

    def __call__(self, context: grpc.AuthMetadataContext, callback: grpc.AuthMetadataPluginCallback) -> None:
        """Implements authentication by passing metadata to a callback.

        This method will be invoked asynchronously in a separate thread.

        Args:
          context: An AuthMetadataContext providing information on the RPC that
            the plugin is being called to authenticate.
          callback: An AuthMetadataPluginCallback to be invoked either
            synchronously or asynchronously.
        """
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
