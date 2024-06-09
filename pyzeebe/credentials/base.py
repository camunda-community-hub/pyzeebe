import abc

from pyzeebe.credentials.typing import AuthMetadata, CallContext


class CredentialsABC(abc.ABC):
    """A specification for credentials manager. Passed to :py:class:`AuthMetadataPlugin`."""

    @abc.abstractmethod
    def get_auth_metadata(self, context: CallContext) -> AuthMetadata:
        """
        Args:
            context (grpc.AuthMetadataContext): Provides information to call credentials metadata plugins.

        Returns:
            Tuple[Tuple[str, Union[str, bytes]], ...]: The `metadata` used to construct the :py:class:`grpc.CallCredentials`.
        """
        raise NotImplementedError
