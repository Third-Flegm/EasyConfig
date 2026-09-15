"""Core configuration primitives."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Iterator
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when configuration data cannot be loaded or accessed."""


class Config(Mapping[str, Any]):
    """Simple, layered configuration with optional environment overrides.

    Later sources override earlier sources. Nested values can be accessed with
    dotted keys, for example ``config.get("database.host")``. Use ``set`` to
    change a value and ``save`` to write it to a JSON file.
    """

    def __init__(self, *sources: Mapping[str, Any], env_prefix: str | None = None):
        self._data: dict[str, Any] = {}
        self._env_prefix = env_prefix
        for source in sources:
            self._merge(self._data, source)

        if env_prefix:
            self._apply_environment(env_prefix)

    @classmethod
    def from_file(
        cls, path: str | os.PathLike[str], *, env_prefix: str | None = None
    ) -> "Config":
        """Load a JSON or TOML file, creating an empty file when it is missing."""
        file_path = Path(path)
        if file_path.suffix.lower() not in {".json", ".toml"}:
            raise ConfigError("Configuration files must use .json or .toml")

        try:
            text = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            config = cls()
            config.save(file_path)
            if env_prefix:
                config._apply_environment(env_prefix)
            return config
        except OSError as exc:
            raise ConfigError(f"Could not read configuration file: {file_path}") from exc

        try:
            if file_path.suffix.lower() == ".json":
                values = json.loads(text)
            elif file_path.suffix.lower() == ".toml":
                import tomllib

                values = tomllib.loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ConfigError(f"Invalid configuration file: {file_path}") from exc

        if not isinstance(values, Mapping):
            raise ConfigError("The configuration file must contain an object/table")
        return cls(values, env_prefix=env_prefix)

    def save(self, path: str | os.PathLike[str] = "config.json") -> Path:
        """Save the current configuration as formatted JSON."""
        file_path = Path(path)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(
                json.dumps(self._data, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except (OSError, TypeError) as exc:
            raise ConfigError(f"Could not save configuration file: {file_path}") from exc
        return file_path

    def set(self, key: str, value: Any) -> None:
        """Set a value using a dotted key, such as ``database.port``."""
        if not key or key.endswith(".") or key.startswith("."):
            raise ConfigError("Configuration keys cannot be empty")
        self._set_nested(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Return a value by dotted key, or ``default`` when it is missing."""
        current: Any = self._data
        for part in key.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return default
            current = current[part]
        return current

    def require(self, key: str) -> Any:
        """Return a required value or raise ``ConfigError`` if it is missing."""
        value = self.get(key)
        if value is None:
            raise ConfigError(f"Missing required configuration value: {key}")
        return value

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @staticmethod
    def _merge(target: dict[str, Any], source: Mapping[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, Mapping) and isinstance(target.get(key), dict):
                Config._merge(target[key], value)
            elif isinstance(value, Mapping):
                target[key] = dict(value)
            else:
                target[key] = value

    def _apply_environment(self, prefix: str) -> None:
        for name, raw_value in os.environ.items():
            if not name.startswith(prefix):
                continue
            key = name[len(prefix) :].lower().replace("__", ".")
            if key:
                self._set_nested(key, self._parse_value(raw_value))

    def _set_nested(self, key: str, value: Any) -> None:
        target = self._data
        parts = key.split(".")
        for part in parts[:-1]:
            existing = target.get(part)
            if not isinstance(existing, dict):
                existing = {}
                target[part] = existing
            target = existing
        target[parts[-1]] = value

    @staticmethod
    def _parse_value(value: str) -> Any:
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
