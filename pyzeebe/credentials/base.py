import abc

from pyzeebe.credentials.typing import AuthMetadata, CallContext


class Credentials(abc.ABC):
    @abc.abstractmethod
    def get_auth_metadata(self, context: CallContext) -> AuthMetadata:
        raise NotImplementedError
