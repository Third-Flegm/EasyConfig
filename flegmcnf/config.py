"""Core configuration primitives."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator, Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from ._environment import apply_environment
from ._merge import delete_nested, merge_dicts, set_nested_in
from ._paths import atomic_write, path_from_caller
from ._validation import parse_value, validate_all, validate_key, validate_value


MISSING = object()


class ConfigError(ValueError):
    """Raised when configuration data cannot be loaded or accessed."""


class Config(Mapping[str, Any]):
    """Simple, layered configuration with optional environment overrides."""

    def __init__(
        self,
        *sources: Mapping[str, Any],
        env_prefix: str | None = None,
        schema: Mapping[str, type | tuple[type, ...]] | None = None,
        _validate_schema: bool = True,
    ):
        self._data: dict[str, Any] = {}
        self._base_data: dict[str, Any] = {}
        self._env_prefix = env_prefix
        self._schema = dict(schema or {})
        self._path: Path | None = None
        self._environment_keys: set[str] = set()
        for source in sources:
            merge_dicts(self._data, source)

        self._base_data = deepcopy(self._data)
        if env_prefix:
            apply_environment(self._data, env_prefix, self._environment_keys)
        if _validate_schema:
            self._validate_all()

    @classmethod
    def from_file(
        cls,
        path: str | os.PathLike[str],
        *,
        env_prefix: str | None = None,
        schema: Mapping[str, type | tuple[type, ...]] | None = None,
    ) -> "Config":
        """Load a JSON or TOML file, creating an empty file when it is missing."""
        file_path = path_from_caller(path)
        if file_path.suffix.lower() not in {".json", ".toml"}:
            raise ConfigError(f"{file_path}: configuration files must use .json or .toml")

        try:
            text = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            config = cls(env_prefix=env_prefix, schema=schema)
            config._path = file_path
            config._schema = dict(schema or {})
            if file_path.suffix.lower() == ".json":
                config.save(file_path)
            else:
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    atomic_write(file_path, "")
                except OSError as exc:
                    raise ConfigError(f"{file_path}: could not create configuration file") from exc
            return config
        except OSError as exc:
            raise ConfigError(f"{file_path}: could not read configuration file") from exc

        try:
            if file_path.suffix.lower() == ".json":
                values = json.loads(text)
            elif file_path.suffix.lower() == ".toml":
                try:
                    import tomllib
                except ModuleNotFoundError:
                    import tomli as tomllib

                values = tomllib.loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ConfigError(f"{file_path}: invalid configuration file ({exc})") from exc

        if not isinstance(values, Mapping):
            raise ConfigError(f"{file_path}: configuration must contain an object/table")

        config = cls(values, env_prefix=env_prefix, schema=schema, _validate_schema=False)
        config._path = file_path
        config._schema = dict(schema or {})
        config._validate_all()
        return config

    def reload(self) -> "Config":
        """Reload this configuration from the file it was created from."""
        if self._path is None:
            raise ConfigError("Cannot reload a configuration that was not loaded from a file")
        refreshed = type(self).from_file(
            self._path, env_prefix=self._env_prefix, schema=self._schema
        )
        self._data = refreshed._data
        self._base_data = refreshed._base_data
        self._environment_keys = refreshed._environment_keys
        return self

    def save(self, path: str | os.PathLike[str] | None = None) -> Path:
        """Atomically save the current configuration as formatted JSON."""
        if path is None and self._path is not None:
            file_path = self._path
        else:
            file_path = path_from_caller(path or "config.json")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(self._base_data, indent=2, sort_keys=True) + "\n"
            atomic_write(file_path, content)
            self._path = file_path
        except (OSError, TypeError) as exc:
            raise ConfigError(f"{file_path}: could not save configuration file") from exc
        return file_path

    def set(self, key: str, value: Any) -> None:
        """Set a value using a dotted key, such as ``database.port``."""
        validate_key(key)
        validate_value(key, value, self._schema)
        set_nested_in(self._data, key, value)
        if key not in self._environment_keys:
            set_nested_in(self._base_data, key, value)

    def delete(self, key: str) -> bool:
        """Delete a setting and return ``True`` if it existed."""
        validate_key(key)
        parts = key.split(".")
        current: Any = self._data
        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        if not isinstance(current, dict) or parts[-1] not in current:
            return False
        del current[parts[-1]]
        if key not in self._environment_keys:
            delete_nested(self._base_data, parts)
        return True

    def get(self, key: str, default: Any = MISSING) -> Any:
        """Return a value by dotted key, or ``default`` when it is missing."""
        current: Any = self._data
        for part in key.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return default
            current = current[part]
        return current

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return self.get(key, MISSING) is not MISSING

    def setdefault(self, key: str, default: Any = None) -> Any:
        """Return an existing value or set and return a default."""
        if key in self:
            return self.get(key)
        self.set(key, default)
        return default

    def update(self, other: Mapping[str, Any] | None = None, **kwargs: Any) -> None:
        """Merge mapping values using dotted keys and nested dictionary updates."""
        values: dict[str, Any] = {}
        if other is not None:
            if isinstance(other, Mapping):
                values.update(dict(other))
            else:
                for key, value in other:
                    values[key] = value
        values.update(kwargs)

        for key, value in values.items():
            if isinstance(key, str) and "." in key:
                self.set(key, value)
                continue
            if isinstance(value, Mapping):
                existing = self.get(key, MISSING)
                if isinstance(existing, Mapping):
                    merged = deepcopy(existing)
                    merge_dicts(merged, value)
                    self.set(key, merged)
                else:
                    self.set(key, dict(value))
            else:
                self.set(key, value)

    def to_dict(self) -> dict[str, Any]:
        """Return a deep, independent copy as a normal Python dictionary."""
        return deepcopy(self._data)

    def require(self, key: str) -> Any:
        """Return a required value or raise ``ConfigError`` if it is missing."""
        value = self.get(key, MISSING)
        if value is MISSING or value is None:
            source = f" in {self._path}" if self._path else ""
            raise ConfigError(f"Missing required configuration value: {key}{source}")
        return value

    def __getitem__(self, key: str) -> Any:
        value = self.get(key, MISSING)
        if value is MISSING:
            raise KeyError(key)
        return value

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        if not self.delete(key):
            raise KeyError(key)

    @staticmethod
    def _set_nested(key: str, value: Any, target: dict[str, Any]) -> None:
        set_nested_in(target, key, value)

    @staticmethod
    def _delete_nested(target: dict[str, Any], parts: list[str]) -> None:
        delete_nested(target, parts)

    @staticmethod
    def _parse_value(value: str) -> Any:
        return parse_value(value)

    def _apply_environment(self, prefix: str) -> None:
        apply_environment(self._data, prefix, self._environment_keys)

    def _validate_all(self) -> None:
        for key in self._schema:
            value = self.get(key, MISSING)
            if value is not MISSING:
                self._validate_value(key, value)

    def _validate_value(self, key: str, value: Any) -> None:
        expected = self._schema.get(key)
        if expected is not None and not isinstance(value, expected):
            source = f" in {self._path}" if self._path else ""
            expected_name = getattr(expected, "__name__", str(expected))
            raise ConfigError(
                f"Invalid value for '{key}'{source}: expected {expected_name}, "
                f"got {type(value).__name__}"
            )

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key or any(not part for part in key.split(".")):
            raise ConfigError("Configuration keys cannot be empty")

    @staticmethod
    def _validate_key(key: str) -> None:
        validate_key(key)

    @staticmethod
    def _merge(target: dict[str, Any], source: Mapping[str, Any]) -> None:
        merge_dicts(target, source)

    @staticmethod
    def _set_nested_in(target: dict[str, Any], key: str, value: Any) -> None:
        set_nested_in(target, key, value)
