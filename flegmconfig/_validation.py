from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_MISSING = object()


def _lookup_nested(data: Mapping[str, Any], key: str) -> Any:
    current: Any = data
    for part in key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return _MISSING
        current = current[part]
    return current


def validate_key(key: str) -> None:
    if not key or any(not part for part in key.split(".")):
        raise ValueError("Configuration keys cannot be empty")


def validate_value(key: str, value: Any, schema: Mapping[str, type | tuple[type, ...]] | None) -> None:
    expected = None if schema is None else schema.get(key)
    if expected is not None and not isinstance(value, expected):
        expected_name = getattr(expected, "__name__", str(expected))
        raise TypeError(
            f"Invalid value for '{key}': expected {expected_name}, got {type(value).__name__}"
        )


def validate_all(data: Mapping[str, Any], schema: Mapping[str, type | tuple[type, ...]] | None) -> None:
    if schema is None:
        return
    for key in schema:
        value = _lookup_nested(data, key)
        if value is not _MISSING:
            validate_value(key, value, schema)


def parse_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value
