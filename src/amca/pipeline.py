"""Small orchestration helpers shared by CLI operations."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .constructor import construct
from .models import CandidateGraph, MachineSpec, VerificationReport
from .specification import load_spec
from .verifier import verify_candidate


def prepare(path: str | Path) -> tuple[MachineSpec, CandidateGraph, VerificationReport]:
    spec = load_spec(path)
    graph = construct(spec)
    verification = verify_candidate(graph)
    return spec, graph, verification


def verify_value(value: Any) -> VerificationReport:
    return verify_candidate(value)
