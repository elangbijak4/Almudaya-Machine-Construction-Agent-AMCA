"""Bounded, safe YAML loading for machine specifications."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from yaml.events import AliasEvent
from yaml.nodes import MappingNode
from yaml.tokens import AnchorToken, AliasToken

from .errors import InputError, SpecificationError

MAX_SPEC_BYTES = 65_536


class _StrictSafeLoader(yaml.SafeLoader):
    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(AliasEvent):
            event = self.peek_event()
            raise yaml.constructor.ConstructorError(
                None, None, "YAML aliases are not supported", event.start_mark
            )
        return super().compose_node(parent, index)


def _construct_mapping(loader: _StrictSafeLoader, node: MappingNode, deep: bool = False) -> dict[str, Any]:
    if not isinstance(node, MappingNode):
        raise yaml.constructor.ConstructorError(None, None, "Expected a mapping", node.start_mark)
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if type(key) is not str:
            raise yaml.constructor.ConstructorError(None, None, "Mapping keys must be strings", key_node.start_mark)
        if key in result:
            raise yaml.constructor.ConstructorError(None, None, f"Duplicate key {key!r}", key_node.start_mark)
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def load_spec(path_or_bytes: str | Path | bytes):
    """Read and validate a single machine specification document."""
    if isinstance(path_or_bytes, bytes):
        raw = path_or_bytes
    else:
        try:
            raw = Path(path_or_bytes).read_bytes()
        except OSError as exc:
            raise InputError(f"Could not read specification: {exc.strerror or exc.__class__.__name__}") from None
    if len(raw) > MAX_SPEC_BYTES:
        raise SpecificationError("Specification exceeds 65,536 bytes", path="$")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise InputError("Specification must be valid UTF-8", path="$") from None
    try:
        for token in yaml.scan(text, Loader=_StrictSafeLoader):
            if isinstance(token, (AnchorToken, AliasToken)):
                raise SpecificationError("YAML anchors and aliases are not supported", path="$")
        value = yaml.load(text, Loader=_StrictSafeLoader)
    except AMCA_SAFE_YAML_ERRORS as exc:
        if isinstance(exc, SpecificationError):
            raise
        raise InputError(f"Invalid YAML: {str(exc).splitlines()[0]}", path="$") from None
    if not isinstance(value, dict):
        raise SpecificationError("Specification root must be a mapping", path="$")
    from .schema import validate_spec_mapping

    return validate_spec_mapping(value)


AMCA_SAFE_YAML_ERRORS = (yaml.YAMLError, SpecificationError)
