# EasyConfig Syntax

This page shows the complete public syntax of EasyConfig.

## Import

```python
from easyconfig import Config, ConfigError
```

`Config` manages your settings. `ConfigError` is raised when a configuration
file cannot be read, saved, or when a required value is missing.

## Load `config.json`

```python
config = Config.from_file("config.json")
```

If the file does not exist, EasyConfig creates it with an empty object:

```json
{}
```

The file can also be inside another folder:

```python
config = Config.from_file("settings/config.json")
```

Missing folders are created automatically.

## Read a value

Use bracket syntax for a value you expect to exist:

```python
app_name = config["app_name"]
port = config["database.port"]
```

A dot means a nested JSON object. For example, `database.port` reads this:

```json
{
  "database": {
    "port": 5432
  }
}
```

Use `get` when a value might not exist:

```python
debug = config.get("debug")
port = config.get("database.port", 5432)
```

The second argument is the default value.

## Require a value

Use `require` when your program cannot work without a setting:

```python
secret_key = config.require("secret_key")
```

If the value is missing or `null`, EasyConfig raises `ConfigError`.

## Change a value

Use `set` with a key and a value:

```python
config.set("debug", True)
config.set("database.port", 5433)
config.set("app.name", "my-service")
```

Nested objects are created automatically when needed.

## Save changes

Save to `config.json`:

```python
config.save("config.json")
```

You can save to another JSON path too:

```python
config.save("backup/config.json")
```

`save` creates missing folders and returns the saved `Path`.

## Create settings in Python

You can create a configuration without loading a file:

```python
config = Config(
    {"app": {"name": "my-service"}},
    {"debug": False},
)

config.save("config.json")
```

Later sources override earlier sources. In this example, the second source
would win if both sources contained the same key.

## Environment overrides

Pass a prefix when loading or creating a configuration:

```python
config = Config.from_file("config.json", env_prefix="APP_")
```

These environment variables override values from the file:

```text
APP_DEBUG=true
APP_DATABASE__HOST=db.example.com
APP_DATABASE__PORT=5433
```

Double underscores (`__`) represent nested keys. Environment values are
converted to booleans and numbers when possible.

## JSON and TOML

Both file formats can be loaded:

```python
json_config = Config.from_file("config.json")
toml_config = Config.from_file("config.toml")
```

`save` always writes JSON, even when the configuration was loaded from TOML.

## Loop through top-level settings

A `Config` object behaves like a read-only mapping when reading top-level keys:

```python
for key in config:
    print(key, config[key])

number_of_settings = len(config)
```

## Handle errors

```python
try:
    config = Config.from_file("config.json")
    database_url = config.require("database.url")
except ConfigError as error:
    print(f"Configuration problem: {error}")
```
