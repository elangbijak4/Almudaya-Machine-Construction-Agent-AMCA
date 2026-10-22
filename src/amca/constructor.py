"""Deterministic assembly of an untrusted candidate from a validated spec."""
from __future__ import annotations

from .canonical import sha256
from .models import CandidateGraph, GraphNode, MachineSpec
from .registry import registry_profile


def specification_payload(spec: MachineSpec) -> dict:
    return {
        "schema_version": spec.schema_version,
        "machine_id": spec.machine_id,
        "nodes": [
            {"id": node.id, "component": node.component, "config": node.config}
            for node in sorted(spec.nodes, key=lambda node: node.id)
        ],
        "edges": [edge.as_dict() for edge in sorted(spec.edges)],
    }


def construct(spec: MachineSpec) -> CandidateGraph:
    """Normalize a validated spec; this function does not authorize execution."""
    spec_digest = sha256(specification_payload(spec))
    provisional = CandidateGraph(
        graph_version="1.0",
        machine_id=spec.machine_id,
        nodes=tuple(
            GraphNode(node.id, node.component, node.config)
            for node in sorted(spec.nodes, key=lambda node: node.id)
        ),
        edges=tuple(sorted(spec.edges)),
        specification_sha256=spec_digest,
        candidate_sha256="",
        registry_profile=registry_profile(),
    )
    return CandidateGraph(
        graph_version=provisional.graph_version,
        machine_id=provisional.machine_id,
        nodes=provisional.nodes,
        edges=provisional.edges,
        specification_sha256=provisional.specification_sha256,
        candidate_sha256=sha256(provisional.core_dict()),
        registry_profile=provisional.registry_profile,
    )
