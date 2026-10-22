"""Independent structural and interface verifier."""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Callable

from .canonical import byte_size, sha256, validate_json_value
from .errors import InputError
from .models import CandidateGraph, CheckResult, Edge, VerificationReason, VerificationReport
from .registry import REGISTRY_VERSION, get_component
from .schema import MAX_EDGES, MAX_NODES

VERIFIER_PROFILE = "amca-verifier-v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
CHECK_IDS = (
    "candidate_shape",
    "graph_bounds",
    "unique_node_ids",
    "known_components",
    "edge_endpoints",
    "unique_connections",
    "interface_compatibility",
    "required_inputs",
    "acyclic",
    "registry_profile_binding",
)


def _digest(candidate: object) -> str:
    if not isinstance(candidate, CandidateGraph):
        return "0" * 64
    try:
        return sha256(candidate.core_dict())
    except Exception:
        return "0" * 64


def _check_shape(candidate: object) -> list[VerificationReason]:
    reasons: list[VerificationReason] = []
    if not isinstance(candidate, CandidateGraph):
        return [VerificationReason("candidate_type", "Candidate is not a CandidateGraph")]
    if candidate.graph_version != "1.0":
        reasons.append(VerificationReason("graph_version", "Unsupported graph version"))
    if type(candidate.machine_id) is not str or not candidate.machine_id:
        reasons.append(VerificationReason("machine_id", "Candidate machine_id is malformed"))
    if type(candidate.nodes) is not tuple or any(type(n.id) is not str or type(n.component) is not str or type(n.config) is not dict for n in candidate.nodes):
        reasons.append(VerificationReason("node_shape", "Candidate node data is malformed"))
    if type(candidate.edges) is not tuple or any(not isinstance(e, Edge) for e in candidate.edges):
        reasons.append(VerificationReason("edge_shape", "Candidate edge data is malformed"))
    if not isinstance(candidate.specification_sha256, str) or not _HEX64.fullmatch(candidate.specification_sha256):
        reasons.append(VerificationReason("specification_digest", "Specification digest is malformed"))
    if not isinstance(candidate.candidate_sha256, str) or not _HEX64.fullmatch(candidate.candidate_sha256):
        reasons.append(VerificationReason("candidate_digest", "Candidate digest is malformed"))
    elif candidate.candidate_sha256 != _digest(candidate):
        reasons.append(VerificationReason("candidate_digest_mismatch", "Candidate content does not match its digest"))
    try:
        validate_json_value(candidate.core_dict())
    except Exception:
        reasons.append(VerificationReason("candidate_data_type", "Candidate contains unsupported data values"))
    return reasons


def _check_bounds(candidate: CandidateGraph) -> list[VerificationReason]:
    if len(candidate.nodes) > MAX_NODES or len(candidate.edges) > MAX_EDGES or not candidate.nodes:
        return [VerificationReason("graph_bounds", "Candidate must have 1–64 nodes and at most 128 edges")]
    for node in candidate.nodes:
        if byte_size(node.config) > 16_384:
            return [VerificationReason("config_bounds", "Node config exceeds its bound", node_id=node.id)]
    return []


def _check_unique_ids(candidate: CandidateGraph) -> list[VerificationReason]:
    reasons = []
    seen: set[str] = set()
    identifier = re.compile(r"^[a-z][a-z0-9_-]{0,63}$", re.ASCII)
    if type(candidate.machine_id) is not str or identifier.fullmatch(candidate.machine_id) is None:
        reasons.append(VerificationReason("invalid_machine_id", "Candidate machine_id is malformed"))
    for node in candidate.nodes:
        if type(node.id) is not str or identifier.fullmatch(node.id) is None:
            reasons.append(VerificationReason("invalid_node_id", "Node id is malformed", node_id=str(node.id)))
            continue
        if node.id in seen:
            reasons.append(VerificationReason("duplicate_node_id", f"Duplicate node id {node.id!r}", node_id=node.id))
        seen.add(node.id)
    return reasons


def _check_components(candidate: CandidateGraph) -> list[VerificationReason]:
    reasons = []
    for node in candidate.nodes:
        try:
            get_component(node.component)
        except Exception:
            reasons.append(VerificationReason("unknown_component", f"Unknown component {node.component!r}", node_id=node.id))
    return reasons


def _check_endpoints(candidate: CandidateGraph) -> list[VerificationReason]:
    known = {node.id for node in candidate.nodes}
    reasons = []
    for edge in candidate.edges:
        if edge.source not in known or edge.target not in known:
            reasons.append(VerificationReason("unknown_endpoint", "Edge endpoint does not exist", edge=edge))
        elif edge.source == edge.target:
            reasons.append(VerificationReason("self_edge", "Self-edges are not allowed", edge=edge))
    return reasons


def _check_connections(candidate: CandidateGraph) -> list[VerificationReason]:
    edges_seen: set[Edge] = set()
    inputs_seen: set[tuple[str, str]] = set()
    reasons = []
    for edge in candidate.edges:
        if edge in edges_seen:
            reasons.append(VerificationReason("duplicate_edge", "Duplicate edge", edge=edge))
        edges_seen.add(edge)
        key = (edge.target, edge.input)
        if key in inputs_seen:
            reasons.append(VerificationReason("duplicate_input_connection", "Input port has multiple connections", node_id=edge.target, edge=edge))
        inputs_seen.add(key)
    return reasons


def _port_type(component_id: str, port: str, output: bool) -> str | None:
    definition = get_component(component_id)
    ports = definition.output_ports if output else definition.input_ports
    return ports.get(port)


def _check_interfaces(candidate: CandidateGraph) -> list[VerificationReason]:
    by_id = {node.id: node for node in candidate.nodes}
    reasons = []
    for edge in candidate.edges:
        if edge.source not in by_id or edge.target not in by_id:
            continue
        try:
            out_type = _port_type(by_id[edge.source].component, edge.output, True)
            in_type = _port_type(by_id[edge.target].component, edge.input, False)
        except Exception:
            continue
        if out_type is None:
            reasons.append(VerificationReason("unknown_output_port", f"Unknown output port {edge.output!r}", node_id=edge.source, edge=edge))
        elif in_type is None:
            reasons.append(VerificationReason("unknown_input_port", f"Unknown input port {edge.input!r}", node_id=edge.target, edge=edge))
        elif out_type != in_type:
            reasons.append(VerificationReason("incompatible_ports", f"Port types differ: {out_type} -> {in_type}", edge=edge))
    return reasons


def _check_required_inputs(candidate: CandidateGraph) -> list[VerificationReason]:
    reasons = []
    connected = {(edge.target, edge.input) for edge in candidate.edges}
    for node in candidate.nodes:
        try:
            component = get_component(node.component)
            component.validate_config(node.config, f"nodes.{node.id}.config")
        except Exception as exc:
            reasons.append(VerificationReason("invalid_component_config", str(exc), node_id=node.id))
            continue
        missing = sorted(set(component.input_ports) - {port for target, port in connected if target == node.id})
        if missing:
            reasons.append(VerificationReason("missing_required_input", f"Missing required input port(s): {', '.join(missing)}", node_id=node.id))
        if node.component == "input_source" and any(edge.target == node.id for edge in candidate.edges):
            reasons.append(VerificationReason("source_has_incoming_edge", "input_source cannot have incoming edges", node_id=node.id))
    return reasons


def _check_acyclic(candidate: CandidateGraph) -> list[VerificationReason]:
    nodes = {node.id for node in candidate.nodes}
    incoming = {node_id: 0 for node_id in nodes}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in candidate.edges:
        if edge.source in nodes and edge.target in nodes:
            incoming[edge.target] += 1
            outgoing[edge.source].append(edge.target)
    ready = sorted(node_id for node_id, degree in incoming.items() if degree == 0)
    visited = 0
    while ready:
        node_id = ready.pop(0)
        visited += 1
        for target in sorted(outgoing[node_id]):
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
                ready.sort()
    if visited != len(nodes):
        return [VerificationReason("cycle_detected", "Candidate graph contains a directed cycle")]
    return []


def _check_registry(candidate: CandidateGraph) -> list[VerificationReason]:
    if candidate.registry_profile != REGISTRY_VERSION:
        return [VerificationReason("registry_profile_mismatch", "Candidate registry profile is not current")]
    return []


_CHECKS: tuple[tuple[str, Callable[[CandidateGraph], list[VerificationReason]]], ...] = (
    ("candidate_shape", _check_shape),
    ("graph_bounds", _check_bounds),
    ("unique_node_ids", _check_unique_ids),
    ("known_components", _check_components),
    ("edge_endpoints", _check_endpoints),
    ("unique_connections", _check_connections),
    ("interface_compatibility", _check_interfaces),
    ("required_inputs", _check_required_inputs),
    ("acyclic", _check_acyclic),
    ("registry_profile_binding", _check_registry),
)


def verify_candidate(candidate: CandidateGraph) -> VerificationReport:
    digest = _digest(candidate)
    check_results: list[CheckResult] = []
    reasons: list[VerificationReason] = []
    any_failed = False
    any_inconclusive = False
    for check_id, check in _CHECKS:
        try:
            failures = check(candidate)  # type: ignore[arg-type]
            status = "failed" if failures else "passed"
            reasons.extend(failures)
            any_failed |= bool(failures)
        except Exception:
            status = "inconclusive"
            any_inconclusive = True
            reasons.append(VerificationReason("check_inconclusive", f"Required check {check_id} could not be completed"))
        check_results.append(CheckResult(check_id, status, {"reason_count": len(failures) if status != "inconclusive" else 1}))
    status = "rejected" if any_failed else "inconclusive" if any_inconclusive else "verified"
    return VerificationReport(
        status=status,
        candidate_sha256=digest,
        profile_id=VERIFIER_PROFILE,
        checks=tuple(check_results),
        reasons=tuple(reasons),
        assumptions=(f"Trusted component registry profile: {REGISTRY_VERSION}", "Verification checks declared structure and interfaces only."),
    )
