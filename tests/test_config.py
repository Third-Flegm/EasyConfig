import json

import pytest

from easyconfig import Config, ConfigError


def test_sources_merge_and_dotted_lookup():
    config = Config(
        {"app": {"name": "demo", "debug": False}},
        {"app": {"debug": True}},
    )

    assert config.get("app.name") == "demo"
    assert config["app.debug"] is True
    assert config.get("missing", "fallback") == "fallback"


def test_environment_overrides_and_parses_values(monkeypatch):
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_DATABASE__PORT", "5432")

    config = Config({"debug": False}, env_prefix="APP_")

    assert config["debug"] is True
    assert config["database.port"] == 5432


def test_json_file_loading(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"name": "demo"}), encoding="utf-8")

    assert Config.from_file(path)["name"] == "demo"


def test_missing_file_is_created_with_empty_configuration(tmp_path):
    path = tmp_path / "new" / "config.json"

    config = Config.from_file(path)

    assert path.exists()
    assert path.read_text(encoding="utf-8") == "{}\n"
    assert len(config) == 0


def test_configuration_can_be_saved_and_loaded(tmp_path):
    path = tmp_path / "config.json"
    config = Config({"app": {"name": "demo"}, "port": 8000})
    config.set("app.name", "updated-demo")
    config.save(path)

    assert Config.from_file(path)["app.name"] == "updated-demo"
    assert Config.from_file(path)["port"] == 8000


def test_require_raises_for_missing_value():
    with pytest.raises(ConfigError):
        Config().require("database.host")
