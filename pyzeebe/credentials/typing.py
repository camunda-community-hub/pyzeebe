from typing import Protocol, Union

AuthMetadata = tuple[tuple[str, Union[str, bytes]], ...]


class CallContext(Protocol):
    service_url: str
    method_name: str
