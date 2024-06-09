import grpc

from pyzeebe.credentials.base import CredentialsABC


class AuthMetadataPlugin(grpc.AuthMetadataPlugin):  # type: ignore[misc]
    """Custom authentication plugin with exception catching.

    Args:
        credentials (CredentialsABC): A credentials manager.
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
            callback((), e)
        else:
            callback(metadata, None)
