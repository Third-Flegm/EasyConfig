from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def merge_dicts(target: dict[str, Any], source: Mapping[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), dict):
            merge_dicts(target[key], value)
        elif isinstance(value, Mapping):
            target[key] = dict(value)
        else:
            target[key] = value


def set_nested_in(target: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    for part in parts[:-1]:
        existing = target.get(part)
        if not isinstance(existing, dict):
            existing = {}
            target[part] = existing
        target = existing
    target[parts[-1]] = value


def delete_nested(target: dict[str, Any], parts: list[str]) -> None:
    current: Any = target
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return
        current = current[part]
    if isinstance(current, dict):
        current.pop(parts[-1], None)
