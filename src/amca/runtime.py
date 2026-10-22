"""Fail-closed execution of verified candidates through the fixed registry."""
from __future__ import annotations

from typing import Any

from . import RUNTIME_VERSION
from .canonical import byte_size, sha256, validate_json_value
from .errors import AMCAError, ComponentFailure, InputError, RuntimeRefused
from .models import CandidateGraph, VerificationReport
from .registry import REGISTRY_VERSION, get_component
from .schema import MAX_INPUT_BYTES, MAX_OUTPUT_BYTES
from .scheduler import topological_order
from .verifier import VERIFIER_PROFILE, verify_candidate


def _validate_external_inputs(inputs: Any, candidate: CandidateGraph) -> None:
    if type(inputs) is not dict:
        raise InputError("Runtime inputs must be an object", path="inputs")
    try:
        validate_json_value(inputs)
        size = byte_size(inputs)
    except AMCAError as exc:
        raise InputError(exc.message, path=exc.path) from None
    if size > MAX_INPUT_BYTES:
        raise InputError("Runtime input object exceeds 16,384 bytes", path="inputs")
    for node in candidate.nodes:
        if node.component != "input_source":
            continue
        key = node.config.get("input_key")
        if type(key) is not str or key not in inputs:
            raise InputError(f"Required external input {key!r} is missing", path=f"inputs.{key}")
        value = inputs[key]
        if type(value) is not str or not value:
            raise InputError("Selected input must be a nonempty string", path=f"inputs.{key}")
        if len(value.encode("utf-8")) > MAX_INPUT_BYTES:
            raise InputError("Selected input exceeds 16,384 UTF-8 bytes", path=f"inputs.{key}")


def _report_matches(supplied: VerificationReport, actual: VerificationReport) -> bool:
    return supplied.as_dict() == actual.as_dict()


def run(candidate: CandidateGraph, verification: VerificationReport, inputs: dict[str, Any]) -> dict[str, Any]:
    """Run only if fresh verification exactly matches the supplied evidence."""
    fresh = verify_candidate(candidate)
    if (
        verification.status != "verified"
        or verification.profile_id != VERIFIER_PROFILE
        or verification.candidate_sha256 != fresh.candidate_sha256
        or fresh.status != "verified"
        or not _report_matches(verification, fresh)
    ):
        return _refused_record(candidate, inputs, fresh, "Candidate lacks current matching verified evidence")
    if candidate.registry_profile != REGISTRY_VERSION:
        return _refused_record(candidate, inputs, fresh, "Candidate registry profile is not current")
    _validate_external_inputs(inputs, candidate)
    order = topological_order(candidate)
    node_by_id = {node.id: node for node in candidate.nodes}
    incoming_edges: dict[str, list[Any]] = {node_id: [] for node_id in node_by_id}
    for edge in candidate.edges:
        incoming_edges[edge.target].append(edge)
    outputs: dict[str, dict[str, Any]] = {}
    node_records: list[dict[str, Any]] = []
    ran_order: list[str] = []
    failed_node: str | None = None
    for index, node_id in enumerate(order):
        node = node_by_id[node_id]
        if failed_node is not None:
            node_records.append({
                "node_id": node_id,
                "component": node.component,
                "status": "skipped",
            })
            continue
        values: dict[str, Any] = {}
        for edge in incoming_edges[node_id]:
            values[edge.input] = outputs[edge.source][edge.output]
        try:
            component = get_component(node.component)
            if node.component == "input_source":
                key = node.config["input_key"]
                component_input = {key: inputs[key]}
            else:
                component_input = values
            input_bytes = byte_size(component_input)
            if input_bytes > MAX_INPUT_BYTES:
                raise ComponentFailure("Component input exceeds 16,384 bytes")
            ran_order.append(node_id)
            result = component.function(node.config, component_input)
            if type(result) is not dict or set(result) != set(component.output_ports):
                raise ComponentFailure("Component returned an invalid output port mapping")
            validate_json_value(result)
            for port, value in result.items():
                if not _value_matches(component.output_ports[port], value):
                    raise ComponentFailure(f"Output port {port!r} has an invalid value type")
            if byte_size(result) > MAX_OUTPUT_BYTES:
                raise ComponentFailure("Component output exceeds 65,536 bytes")
            outputs[node_id] = result
            node_records.append({
                "node_id": node_id,
                "component": node.component,
                "status": "succeeded",
                "output_summary": {
                    "sha256": sha256(result),
                    "byte_size": byte_size(result),
                    "value_type": "object",
                    **_safe_summary(node.component, result),
                },
            })
        except Exception as exc:
            failed_node = node_id
            message = exc.message if isinstance(exc, AMCAError) else "Component raised an unexpected error"
            category = exc.category if isinstance(exc, AMCAError) else "component_failed"
            node_records.append({
                "node_id": node_id,
                "component": node.component,
                "status": "failed",
                "error": {"category": category, "message": message[:500]},
            })
    status = "failed" if failed_node else "succeeded"
    return {
        "record_version": "1.0",
        "machine_id": candidate.machine_id,
        "specification_sha256": candidate.specification_sha256,
        "candidate_sha256": candidate.candidate_sha256,
        "inputs_sha256": sha256(inputs),
        "verification": verification.as_dict(),
        "run_status": status,
        "execution_order": ran_order,
        "node_records": node_records,
        "registry_version": REGISTRY_VERSION,
        "runtime_version": RUNTIME_VERSION,
    }


def _value_matches(value_type: str, value: Any) -> bool:
    return (value_type == "string" and type(value) is str) or (
        value_type == "object" and type(value) is dict
    )


def _refused_record(
    candidate: CandidateGraph,
    inputs: Any,
    verification: VerificationReport,
    reason: str,
) -> dict[str, Any]:
    input_digest = sha256(inputs) if _is_json_value(inputs) else "0" * 64
    is_candidate = isinstance(candidate, CandidateGraph)
    return {
        "record_version": "1.0",
        "machine_id": candidate.machine_id if is_candidate else "unknown",
        "specification_sha256": candidate.specification_sha256 if is_candidate else "0" * 64,
        "candidate_sha256": _candidate_digest(candidate),
        "inputs_sha256": input_digest,
        "verification": verification.as_dict(),
        "run_status": "refused",
        "refusal_reason": reason,
        "execution_order": [],
        "node_records": [],
        "registry_version": REGISTRY_VERSION,
        "runtime_version": RUNTIME_VERSION,
    }


def _candidate_digest(candidate: CandidateGraph) -> str:
    try:
        return sha256(candidate.core_dict())
    except Exception:
        return "0" * 64


def _is_json_value(value: Any) -> bool:
    try:
        validate_json_value(value)
        return True
    except Exception:
        return False


def _safe_summary(component_id: str, result: dict[str, Any]) -> dict[str, Any]:
    """Expose bounded derived counts/summaries, never raw source text."""
    if component_id in {"analysis_a", "analysis_b"}:
        finding = result.get("finding")
        if type(finding) is dict:
            return {"safe_summary": finding}
    if component_id == "aggregate_results" and type(result.get("summary")) is str:
        return {"safe_summary": {"summary": result["summary"]}}
    if component_id == "generate_report" and type(result.get("report")) is dict:
        report = result["report"]
        if type(report.get("summary")) is str:
            return {"safe_summary": {"summary": report["summary"]}}
    return {}
