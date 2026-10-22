#!/usr/bin/env python3
"""Validate AMCA Waterfall scaffold consistency and phase-transition gates.

Requires PyYAML: python -m pip install -r requirements-dev.txt
This validator checks recorded facts; it cannot replace project-owner review.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Run: python -m pip install -r requirements-dev.txt", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
VALID_CRITERION_STATES = {"pending", "complete", "not_applicable"}
VALID_APPROVAL_STATES = {"pending", "approved", "rejected"}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-scaffold", action="store_true", help="check files, schema shape, and status consistency")
    parser.add_argument("--phase", choices=[f"P{i}" for i in range(7)], help="evaluate a phase gate; exit nonzero if transition is not ready")
    args = parser.parse_args()
    if not args.check_scaffold and not args.phase:
        args.check_scaffold = True

    errors: list[str] = []
    warnings: list[str] = []
    try:
        orchestration = load_yaml(ROOT / "orchestration.yaml")
        gates = load_yaml(ROOT / "workflow/gate-records.yaml")
    except Exception as exc:
        print(f"ERROR: could not load workflow YAML: {exc}", file=sys.stderr)
        return 2

    phase_list = orchestration.get("workflow", {}).get("phases", [])
    phase_by_id = {item.get("id"): item for item in phase_list}
    status_text = (ROOT / "docs/phase-status.md").read_text(encoding="utf-8")

    # Check scaffold integrity and exact synchronization of machine statuses.
    for required in ["README.md", "agent.md", "CHANGELOG.md", "workflow/README.md", "docs/README.md", "docs/phase-status.md", "docs/traceability-matrix.md", "docs/change-control.md"]:
        if not (ROOT / required).exists():
            errors.append(f"Required scaffold path is missing: {required}")
    for phase_id, phase in phase_by_id.items():
        if phase.get("status") not in status_text:
            errors.append(f"Machine status for {phase_id} ({phase.get('status')!r}) is not reflected in docs/phase-status.md")
        for path_text in phase.get("deliverables", []):
            path = ROOT / path_text
            if not path.exists():
                errors.append(f"Declared deliverable path for {phase_id} is missing: {path_text}")
        record = gates.get("phases", {}).get(phase_id)
        if not isinstance(record, dict):
            errors.append(f"Missing gate record for {phase_id}")
            continue
        expected_ids = {c.get("id") for c in phase.get("exit_criteria", [])}
        recorded_ids = set(record.get("criteria", {}).keys())
        if expected_ids != recorded_ids:
            errors.append(f"Exit-criterion IDs differ for {phase_id}: orchestration={sorted(expected_ids)}, gate-records={sorted(recorded_ids)}")
    if gates.get("project_id") != orchestration.get("project", {}).get("id"):
        errors.append("Project ID mismatch between orchestration.yaml and gate-records.yaml")
    if gates.get("scaffold_version") != orchestration.get("project", {}).get("version"):
        errors.append("Scaffold version mismatch between orchestration.yaml and gate-records.yaml")

    if args.phase:
        phase_id = args.phase
        if phase_id not in phase_by_id:
            errors.append(f"Unknown phase {phase_id}")
        else:
            phase = phase_by_id[phase_id]
            record = gates.get("phases", {}).get(phase_id, {})
            for dep_id in phase.get("depends_on", []):
                dep = gates.get("phases", {}).get(dep_id, {})
                if dep.get("approval_status") != "approved":
                    errors.append(f"Dependency {dep_id} has not been human-approved")
            for criterion in phase.get("exit_criteria", []):
                cid = criterion["id"]
                entry = record.get("criteria", {}).get(cid, {})
                state = entry.get("status", "pending")
                if state not in VALID_CRITERION_STATES:
                    errors.append(f"{cid} has invalid status {state!r}")
                if state != "complete":
                    errors.append(f"{cid} is not complete (current status: {state})")
                if not str(entry.get("evidence_path", "")).strip():
                    errors.append(f"{cid} has no evidence_path")
                else:
                    evidence_path = (ROOT / str(entry["evidence_path"])).resolve()
                    if ROOT.resolve() not in evidence_path.parents and evidence_path != ROOT.resolve():
                        errors.append(f"{cid} evidence_path escapes project root")
                    elif not evidence_path.exists():
                        errors.append(f"{cid} evidence file does not exist: {entry['evidence_path']}")
                if not str(entry.get("evidence_summary", "")).strip():
                    errors.append(f"{cid} has no evidence_summary")
            approval = record.get("approval_status", "pending")
            if approval not in VALID_APPROVAL_STATES:
                errors.append(f"{phase_id} has invalid approval_status {approval!r}")
            if approval != "approved":
                errors.append(f"{phase_id} has not been explicitly approved by the project owner")
            for field in ["approved_by", "approved_at", "decision_evidence"]:
                if not str(record.get(field, "")).strip():
                    errors.append(f"{phase_id} approval is missing {field}")
            if approval == "approved" and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(record.get("approved_at", ""))):
                errors.append(f"{phase_id} approved_at must use YYYY-MM-DD")

    if errors:
        print("AMCA workflow validation: BLOCKED")
        for item in errors:
            print(f"- {item}")
        print(f"\n{len(errors)} blocking issue(s); {len(warnings)} warning(s).")
        return 1
    print("AMCA workflow validation: PASS")
    print("Scaffold consistency checks passed. This does not establish software correctness.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
