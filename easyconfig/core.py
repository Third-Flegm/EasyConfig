"""Core configuration primitives."""

from __future__ import annotations

import json
import inspect
import os
import tempfile
from collections.abc import Mapping, Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any


MISSING = object()


class ConfigError(ValueError):
    """Raised when configuration data cannot be loaded or accessed."""


class Config(Mapping[str, Any]):
    """Simple, layered configuration with optional environment overrides.

    Later sources override earlier sources. Nested values can be accessed with
    dotted keys, for example ``config.get("database.host")``. Use ``set`` to
    change a value and ``save`` to write it to a JSON file.
    """

    def __init__(
        self,
        *sources: Mapping[str, Any],
        env_prefix: str | None = None,
        schema: Mapping[str, type | tuple[type, ...]] | None = None,
    ):
        self._data: dict[str, Any] = {}
        self._base_data: dict[str, Any] = {}
        self._env_prefix = env_prefix
        self._schema = dict(schema or {})
        self._path: Path | None = None
        self._environment_keys: set[str] = set()
        for source in sources:
            self._merge(self._data, source)

        self._base_data = deepcopy(self._data)
        if env_prefix:
            self._apply_environment(env_prefix)
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
        file_path = cls._path_from_caller(path)
        if file_path.suffix.lower() not in {".json", ".toml"}:
            raise ConfigError(f"{file_path}: configuration files must use .json or .toml")

        try:
            text = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            config = cls(env_prefix=env_prefix)
            config._path = file_path
            config._schema = dict(schema or {})
            config._validate_all()
            if file_path.suffix.lower() == ".json":
                config.save(file_path)
            else:
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    config._atomic_write(file_path, "")
                except OSError as exc:
                    raise ConfigError(
                        f"{file_path}: could not create configuration file"
                    ) from exc
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
        config = cls(values, env_prefix=env_prefix)
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
            file_path = self._path_from_caller(path or "config.json")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(self._base_data, indent=2, sort_keys=True) + "\n"
            self._atomic_write(file_path, content)
            self._path = file_path
        except (OSError, TypeError) as exc:
            raise ConfigError(f"{file_path}: could not save configuration file") from exc
        return file_path

    @staticmethod
    def _path_from_caller(path: str | os.PathLike[str]) -> Path:
        file_path = Path(path)
        if file_path.is_absolute():
            return file_path

        frame = inspect.currentframe()
        try:
            caller = frame
            while caller is not None:
                caller_name = caller.f_code.co_filename
                if caller_name and not caller_name.startswith("<") and caller_name != __file__:
                    return Path(caller_name).resolve().parent / file_path
                caller = caller.f_back
        finally:
            del frame

        return file_path

    @staticmethod
    def _atomic_write(file_path: Path, content: str) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=file_path.parent, delete=False
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, file_path)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    def set(self, key: str, value: Any) -> None:
        """Set a value using a dotted key, such as ``database.port``."""
        self._validate_key(key)
        self._validate_value(key, value)
        self._set_nested(key, value)
        if key not in self._environment_keys:
            self._set_nested_in(self._base_data, key, value)

    def delete(self, key: str) -> bool:
        """Delete a setting and return ``True`` if it existed."""
        self._validate_key(key)
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
            self._delete_nested(self._base_data, parts)
        return True

    def get(self, key: str, default: Any = MISSING) -> Any:
        """Return a value by dotted key, or ``default`` when it is missing."""
        current: Any = self._data
        for part in key.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return default
            current = current[part]
        return current

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
                self._validate_key(key)
                self._environment_keys.add(key)
                self._set_nested(key, self._parse_value(raw_value))

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

    def _set_nested(self, key: str, value: Any) -> None:
        self._set_nested_in(self._data, key, value)

    @staticmethod
    def _set_nested_in(target: dict[str, Any], key: str, value: Any) -> None:
        parts = key.split(".")
        for part in parts[:-1]:
            existing = target.get(part)
            if not isinstance(existing, dict):
                existing = {}
                target[part] = existing
            target = existing
        target[parts[-1]] = value

    @staticmethod
    def _delete_nested(target: dict[str, Any], parts: list[str]) -> None:
        current: Any = target
        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                return
            current = current[part]
        if isinstance(current, dict):
            current.pop(parts[-1], None)

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
