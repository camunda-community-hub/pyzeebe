from abc import ABC, abstractmethod

from grpc import ChannelCredentials


class BaseCredentials(ABC):
    grpc_credentials: ChannelCredentials

    @abstractmethod
    def get_connection_uri(self) -> str:
        pass
