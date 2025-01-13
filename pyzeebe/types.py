from collections.abc import Mapping, Sequence
from typing import Any, Union

from typing_extensions import TypeAlias

Headers: TypeAlias = Mapping[str, Any]
Unset = "UNSET"

ChannelArgumentType: TypeAlias = Sequence[tuple[str, Any]]

JsonType: TypeAlias = Union[Mapping[str, "JsonType"], Sequence["JsonType"], str, int, float, bool, None]
JsonDictType: TypeAlias = Mapping[str, JsonType]
Variables: TypeAlias = JsonDictType
