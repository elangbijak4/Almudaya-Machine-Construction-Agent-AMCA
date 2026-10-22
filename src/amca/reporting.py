"""Stable JSON serialization for verification and execution evidence."""
from __future__ import annotations

import json
from typing import Any

from .canonical import canonical_json
from .models import VerificationReport


def verification_dict(report: VerificationReport) -> dict[str, Any]:
    return report.as_dict()


def execution_dict(record: dict[str, Any]) -> dict[str, Any]:
    return record


def serialize_report(report: VerificationReport | dict[str, Any], *, pretty: bool = False) -> str:
    value = report.as_dict() if isinstance(report, VerificationReport) else report
    if pretty:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    return canonical_json(value).decode("utf-8")
