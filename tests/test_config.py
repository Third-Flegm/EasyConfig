import json

import pytest

from easyconfig import MISSING, Config, ConfigError
from easyconfig import core


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


def test_environment_overrides_are_not_saved(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"debug": False, "name": "file"}), encoding="utf-8")
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_NAME", "runtime")

    config = Config.from_file(path, env_prefix="APP_")
    assert config["debug"] is True
    assert config["name"] == "runtime"

    config.save(path)

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "debug": False,
        "name": "file",
    }


def test_json_file_loading(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"name": "demo"}), encoding="utf-8")

    assert Config.from_file(path)["name"] == "demo"


def test_malformed_json_includes_filename(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"name": }', encoding="utf-8")

    with pytest.raises(ConfigError, match="broken.json"):
        Config.from_file(path)


def test_missing_file_is_created_with_empty_configuration(tmp_path):
    path = tmp_path / "new" / "config.json"

    config = Config.from_file(path)

    assert path.exists()
    assert path.read_text(encoding="utf-8") == "{}\n"
    assert len(config) == 0


def test_relative_missing_file_is_created_next_to_calling_python_file(tmp_path):
    caller_file = tmp_path / "app.py"
    caller_file.write_text("", encoding="utf-8")
    namespace = {}
    code = compile(
        "from easyconfig import Config\nconfig = Config.from_file('config.json')",
        str(caller_file),
        "exec",
    )

    exec(code, namespace)

    assert (tmp_path / "config.json").exists()


def test_configuration_can_be_saved_and_loaded(tmp_path):
    path = tmp_path / "config.json"
    config = Config({"app": {"name": "demo"}, "port": 8000})
    config.set("app.name", "updated-demo")
    config.save(path)

    assert Config.from_file(path)["app.name"] == "updated-demo"
    assert Config.from_file(path)["port"] == 8000


def test_missing_and_null_values_are_distinguishable():
    config = Config({"empty": None})

    assert config.get("missing", MISSING) is MISSING
    assert config.get("empty", MISSING) is None
    assert config["empty"] is None


def test_schema_validates_types_and_names_setting(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"database": {"port": "5432"}}), encoding="utf-8")

    with pytest.raises(ConfigError, match="database.port.*config.json"):
        Config.from_file(path, schema={"database.port": int})


def test_toml_loading_and_nested_updates(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        '[database]\nhost = "localhost"\nport = 5432\n', encoding="utf-8"
    )

    config = Config.from_file(path)
    config.set("database.port", 5433)

    assert config["database.port"] == 5433
    assert config.to_dict() == {"database": {"host": "localhost", "port": 5433}}


def test_delete_and_to_dict_do_not_share_nested_data():
    config = Config({"database": {"host": "localhost", "port": 5432}})
    values = config.to_dict()
    values["database"]["port"] = 1

    assert config["database.port"] == 5432
    assert config.delete("database.port") is True
    assert config.delete("database.port") is False


def test_reload_reads_changes_from_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"debug": False}), encoding="utf-8")
    config = Config.from_file(path)
    path.write_text(json.dumps({"debug": True}), encoding="utf-8")

    assert config.reload() is config
    assert config["debug"] is True


def test_atomic_save_keeps_original_when_replace_fails(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text('{"old": true}\n', encoding="utf-8")
    config = Config.from_file(path)
    config.set("new", True)

    def fail_replace(source, destination):
        raise OSError("simulated interruption")

    monkeypatch.setattr(core.os, "replace", fail_replace)

    with pytest.raises(ConfigError, match="config.json"):
        config.save(path)

    assert path.read_text(encoding="utf-8") == '{"old": true}\n'


def test_environment_conversion(monkeypatch):
    monkeypatch.setenv("EASYCONFIG_TEST_ENABLED", "false")
    monkeypatch.setenv("EASYCONFIG_TEST_RATIO", "1.5")
    monkeypatch.setenv("EASYCONFIG_TEST_COUNT", "3")
    monkeypatch.setenv("EASYCONFIG_TEST_EMPTY", "null")
    monkeypatch.setenv("EASYCONFIG_TEST_NAME", "demo")

    config = Config(env_prefix="EASYCONFIG_TEST_")

    assert config.to_dict() == {
        "enabled": False,
        "ratio": 1.5,
        "count": 3,
        "empty": None,
        "name": "demo",
    }


def test_update_merges_nested_values_and_replaces_existing_keys():
    config = Config({"database": {"host": "localhost", "port": 5432}, "debug": False})

    config.update({"database": {"port": 5433}, "name": "demo"})
    config.update({"debug": True, "database.host": "db.example.com"})

    assert config.to_dict() == {
        "database": {"host": "db.example.com", "port": 5433},
        "debug": True,
        "name": "demo",
    }


def test_setdefault_and_contains_work_with_dotted_keys():
    config = Config({"database": {"host": "localhost"}})

    assert config.setdefault("database.port", 5432) == 5432
    assert config.setdefault("database.host", "ignored") == "localhost"
    assert "database.port" in config
    assert "database.missing" not in config


def test_install_docs_copies_readme_and_syntax_to_target_directory(tmp_path):
    from easyconfig.docs import install_docs

    target = tmp_path / "copied-docs"
    copied = install_docs(target)

    assert copied == [target / "README.md", target / "Syntax.md"]
    assert (target / "README.md").exists()
    assert (target / "Syntax.md").exists()
    assert "EasyConfig" in (target / "README.md").read_text(encoding="utf-8")
    assert "Environment overrides" in (target / "Syntax.md").read_text(encoding="utf-8")


def test_require_raises_for_missing_value():
    with pytest.raises(ConfigError):
        Config().require("database.host")
