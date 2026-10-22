"""Canonical JSON encoding and size/hash helpers."""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .errors import InputError


def validate_json_value(value: Any, path: str = "$") -> None:
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise InputError("Non-finite numbers are not supported", path=path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise InputError("Object keys must be strings", path=path)
            validate_json_value(item, f"{path}.{key}")
        return
    raise InputError(f"Unsupported JSON value type: {type(value).__name__}", path=path)


def canonical_json(value: Any) -> bytes:
    validate_json_value(value)
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(value: Any) -> str:
    return sha256_bytes(canonical_json(value))


def byte_size(value: Any) -> int:
    return len(canonical_json(value))
