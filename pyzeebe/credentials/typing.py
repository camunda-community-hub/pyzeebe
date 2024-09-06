from typing import Any, Protocol, Sequence, Tuple, Union

ChannelArgumentType = Sequence[
    Tuple[str, Any]
]  # from grpc.aio._typing import ChannelArgumentType  # type: ignore[import-untyped]
AuthMetadata = Tuple[Tuple[str, Union[str, bytes]], ...]


class CallContext(Protocol):
    service_url: str
    method_name: str
