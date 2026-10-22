"""Command-line interface for validating, verifying, and running AMCA graphs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .errors import AMCAError, InputError
from .pipeline import prepare
from .reporting import serialize_report
from .runtime import run
from .specification import load_spec


def _load_inputs(path: str) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise InputError(f"Could not read input JSON: {exc.strerror or exc.__class__.__name__}") from None
    if len(raw) > 16_384:
        raise InputError("Runtime input file exceeds 16,384 bytes", path=path)
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=object_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Invalid JSON number {value}")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise InputError(f"Invalid input JSON: {str(exc).splitlines()[0]}", path=path) from None
    if type(value) is not dict:
        raise InputError("Runtime input JSON root must be an object", path=path)
    return value


def _write(value: Any, output: str | None) -> None:
    rendered = serialize_report(value, pretty=True) if not isinstance(value, str) else value
    if output:
        try:
            Path(output).write_text(rendered + "\n", encoding="utf-8")
        except OSError as exc:
            raise InputError(f"Could not write report: {exc.strerror or exc.__class__.__name__}") from None
    else:
        sys.stdout.write(rendered + "\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="amca", description="Validate and run allowlisted declarative DAGs.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate a machine specification without execution")
    validate.add_argument("spec")
    validate.add_argument("--output")
    verify = sub.add_parser("verify", help="construct and independently verify a candidate graph")
    verify.add_argument("spec")
    verify.add_argument("--output")
    execute = sub.add_parser("run", help="verify and execute a candidate with JSON inputs")
    execute.add_argument("spec")
    execute.add_argument("--inputs", required=True)
    execute.add_argument("--output")
    report = sub.add_parser("report", help="read and canonically display a JSON report")
    report.add_argument("report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            spec = load_spec(args.spec)
            value = {
                "status": "valid",
                "machine_id": spec.machine_id,
                "node_count": len(spec.nodes),
                "edge_count": len(spec.edges),
            }
            _write(value, args.output)
            return 0
        if args.command == "verify":
            _, _, verification = prepare(args.spec)
            _write(verification.as_dict(), args.output)
            return 0 if verification.status == "verified" else 1
        if args.command == "run":
            _, candidate, verification = prepare(args.spec)
            inputs = _load_inputs(args.inputs)
            record = run(candidate, verification, inputs)
            _write(record, args.output)
            return 0 if record["run_status"] == "succeeded" else 1
        if args.command == "report":
            try:
                report_bytes = Path(args.report).read_bytes()
            except OSError as exc:
                raise InputError(f"Could not read report: {exc.strerror or exc.__class__.__name__}") from None
            if len(report_bytes) > 1_048_576:
                raise InputError("Report exceeds 1,048,576 bytes", path=args.report)
            try:
                value = json.loads(report_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise InputError(f"Invalid JSON report: {str(exc).splitlines()[0]}", path=args.report) from None
            if type(value) is not dict:
                raise InputError("Report root must be a JSON object", path=args.report)
            _write(value, None)
            return 0
    except AMCAError as exc:
        sys.stderr.write(json.dumps({"error": exc.to_dict()}, sort_keys=True) + "\n")
        return 2
    except (OSError, ValueError, TypeError) as exc:
        sys.stderr.write(json.dumps({"error": {"category": "internal_error", "message": str(exc)}}) + "\n")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
