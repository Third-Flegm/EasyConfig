from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from ._merge import set_nested_in
from ._validation import parse_value, validate_key


def apply_environment(data: dict[str, Any], prefix: str, env_keys: set[str]) -> None:
    for name, raw_value in os.environ.items():
        if not name.startswith(prefix):
            continue
        key = name[len(prefix) :].lower().replace("__", ".")
        if not key:
            continue
        validate_key(key)
        env_keys.add(key)
        set_nested_in(data, key, parse_value(raw_value))
