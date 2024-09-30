from typing import Any, Mapping, Sequence, Tuple

from typing_extensions import TypeAlias

Headers: TypeAlias = Mapping[str, Any]
Variables: TypeAlias = Mapping[str, Any]

ChannelArgumentType: TypeAlias = Sequence[Tuple[str, Any]]
