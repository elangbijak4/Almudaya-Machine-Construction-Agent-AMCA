"""Immutable record types shared by AMCA modules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(frozen=True)
class NodeSpec:
    id: str
    component: str
    config: dict[str, JsonValue]


@dataclass(frozen=True, order=True)
class Edge:
    source: str
    output: str
    target: str
    input: str

    def as_dict(self) -> dict[str, str]:
        return {"from": self.source, "out": self.output, "to": self.target, "in": self.input}


@dataclass(frozen=True)
class MachineSpec:
    schema_version: str
    machine_id: str
    nodes: tuple[NodeSpec, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class GraphNode:
    id: str
    component: str
    config: dict[str, JsonValue]

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "component": self.component, "config": self.config}


@dataclass(frozen=True)
class CandidateGraph:
    graph_version: str
    machine_id: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[Edge, ...]
    specification_sha256: str
    candidate_sha256: str
    registry_profile: str

    def core_dict(self) -> dict[str, Any]:
        return {
            "graph_version": self.graph_version,
            "machine_id": self.machine_id,
            "nodes": [node.as_dict() for node in self.nodes],
            "edges": [edge.as_dict() for edge in self.edges],
            "specification_sha256": self.specification_sha256,
            "registry_profile": self.registry_profile,
        }

    def as_dict(self) -> dict[str, Any]:
        return {**self.core_dict(), "candidate_sha256": self.candidate_sha256}


@dataclass(frozen=True)
class CheckResult:
    id: str
    status: str
    details: dict[str, JsonValue]

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "status": self.status, "details": self.details}


@dataclass(frozen=True)
class VerificationReason:
    code: str
    message: str
    node_id: str | None = None
    edge: Edge | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.node_id is not None:
            result["node_id"] = self.node_id
        if self.edge is not None:
            result["edge"] = self.edge.as_dict()
        return result


@dataclass(frozen=True)
class VerificationReport:
    status: str
    candidate_sha256: str
    profile_id: str
    checks: tuple[CheckResult, ...]
    reasons: tuple[VerificationReason, ...]
    assumptions: tuple[str, ...]
    report_version: str = "1.0"

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "status": self.status,
            "candidate_sha256": self.candidate_sha256,
            "profile_id": self.profile_id,
            "checks": [check.as_dict() for check in self.checks],
            "reasons": [reason.as_dict() for reason in self.reasons],
            "assumptions": list(self.assumptions),
        }
