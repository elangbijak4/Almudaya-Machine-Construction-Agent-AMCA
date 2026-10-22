"""Strict application-level validation for the P3 data contracts."""
from __future__ import annotations

import re
from typing import Any

from .canonical import byte_size, validate_json_value
from .errors import InputError, SpecificationError
from .models import Edge, MachineSpec, NodeSpec
from .registry import get_component

IDENTIFIER = re.compile(r"^[a-z][a-z0-9_-]{0,63}$", re.ASCII)
MAX_NODES = 64
MAX_EDGES = 128
MAX_CONFIG_BYTES = 16_384
MAX_INPUT_BYTES = 16_384
MAX_OUTPUT_BYTES = 65_536
ROOT_FIELDS = {"schema_version", "machine_id", "nodes", "edges"}
NODE_FIELDS = {"id", "component", "config"}
EDGE_FIELDS = {"from", "out", "to", "in"}


def _object(value: Any, path: str, allowed: set[str], required: set[str] | None = None) -> dict[str, Any]:
    if type(value) is not dict:
        raise SpecificationError("Expected an object", path=path)
    unknown = sorted(set(value) - allowed)
    missing = sorted((required or allowed) - set(value))
    if unknown:
        raise SpecificationError(f"Unknown field {unknown[0]!r}", path=path)
    if missing:
        raise SpecificationError(f"Missing required field {missing[0]!r}", path=path)
    return value


def _identifier(value: Any, path: str) -> str:
    if type(value) is not str or IDENTIFIER.fullmatch(value) is None:
        raise SpecificationError("Expected identifier matching [a-z][a-z0-9_-]{0,63}", path=path)
    return value


def validate_spec_mapping(value: dict[str, Any]) -> MachineSpec:
    root = _object(value, "$", ROOT_FIELDS)
    if type(root["schema_version"]) is not str or root["schema_version"] != "1.0":
        raise SpecificationError("schema_version must be '1.0'", path="$.schema_version")
    machine_id = _identifier(root["machine_id"], "$.machine_id")
    nodes_raw = root["nodes"]
    edges_raw = root["edges"]
    if type(nodes_raw) is not list or not 1 <= len(nodes_raw) <= MAX_NODES:
        raise SpecificationError("nodes must contain between 1 and 64 entries", path="$.nodes")
    if type(edges_raw) is not list or len(edges_raw) > MAX_EDGES:
        raise SpecificationError("edges must contain at most 128 entries", path="$.edges")
    nodes: list[NodeSpec] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(nodes_raw):
        path = f"$.nodes[{index}]"
        item = _object(raw, path, NODE_FIELDS)
        node_id = _identifier(item["id"], f"{path}.id")
        if node_id in seen_ids:
            raise SpecificationError(f"Duplicate node id {node_id!r}", path=f"{path}.id")
        seen_ids.add(node_id)
        component_id = item["component"]
        if type(component_id) is not str:
            raise SpecificationError("component must be a string", path=f"{path}.component")
        component = get_component(component_id)
        config = item["config"]
        try:
            validate_json_value(config, f"{path}.config")
        except InputError as exc:
            raise SpecificationError(exc.message, path=exc.path) from None
        component.validate_config(config, f"{path}.config")
        try:
            config_bytes = byte_size(config)
        except InputError as exc:
            raise SpecificationError(exc.message, path=exc.path) from None
        if config_bytes > MAX_CONFIG_BYTES:
            raise SpecificationError("Component config exceeds 16,384 bytes", path=f"{path}.config")
        nodes.append(NodeSpec(node_id, component_id, config))
    edges: list[Edge] = []
    for index, raw in enumerate(edges_raw):
        path = f"$.edges[{index}]"
        item = _object(raw, path, EDGE_FIELDS)
        source = _identifier(item["from"], f"{path}.from")
        output = _identifier(item["out"], f"{path}.out")
        target = _identifier(item["to"], f"{path}.to")
        input_port = _identifier(item["in"], f"{path}.in")
        edges.append(Edge(source, output, target, input_port))
    try:
        validate_json_value(root)
    except InputError as exc:
        raise SpecificationError(exc.message, path=exc.path) from None
    return MachineSpec("1.0", machine_id, tuple(nodes), tuple(edges))
