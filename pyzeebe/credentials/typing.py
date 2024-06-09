from typing import Protocol, Tuple, Union

AuthMetadata = Tuple[Tuple[str, Union[str, bytes]], ...]


class CallContext(Protocol):
    service_url: str
    method_name: str
