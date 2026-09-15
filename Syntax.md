# EasyConfig Syntax

This page shows the complete public syntax of EasyConfig.

## Import

```python
from easyconfig import MISSING, Config, ConfigError
```

`Config` manages your settings. `ConfigError` is raised when a configuration
file cannot be read, saved, or when a required value is missing.

## Load `config.json`

```python
config = Config.from_file("config.json")
```

For a relative path, EasyConfig looks beside the Python file that called
`from_file`. For example, if `app.py` is in `my_app/`, this creates
`my_app/config.json`. Absolute paths are used exactly as provided.

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

To tell a missing key apart from a key whose value is `null`, use the
`MISSING` sentinel:

```python
value = config.get("optional_value", MISSING)

if value is MISSING:
  print("The setting does not exist")
elif value is None:
  print("The setting exists and is null")
```

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

## Delete a value

```python
was_deleted = config.delete("database.port")
```

`delete` returns `True` when the setting existed and `False` when it was
already missing.

## Save changes

Save to the file that was loaded:

```python
config.save()
```

You can also choose a path explicitly:

```python
config.save("config.json")
```

You can save to another JSON path too:

```python
config.save("backup/config.json")
```

Relative save paths use the calling Python file, unless the config was loaded
from a file and `save()` is called without a path; then it saves to the loaded
file. `save` creates missing folders and returns the saved `Path`.
The file is written atomically, so a stop during saving does not leave a
partially written JSON file.

## Reload a file

Configurations loaded with `from_file` remember their filename:

```python
config.reload()
```

`reload` updates the same object from disk and returns it. A configuration
created directly with `Config(...)` cannot be reloaded until it is saved.

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

## Validate types

Pass a schema when loading a file or creating a configuration:

```python
config = Config.from_file(
  "config.json",
  schema={
    "database.port": int,
    "database.host": str,
    "debug": bool,
  },
)
```

If a value has the wrong type, `ConfigError` includes the setting path and
filename. Types can also be checked when changing values with `set`.

## Convert to a dictionary

Use `to_dict` when another library needs normal Python data:

```python
settings = config.to_dict()
```

The returned dictionary is independent of the config object, so changing it
does not change the configuration.

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
Python 3.11+ uses the standard-library `tomllib`. Python 3.10 uses the
automatically installed `tomli` backport. No `tomli-w` package is required
because EasyConfig writes JSON rather than TOML.

## Interactive example

Run the menu example from the project root:

```powershell
python -m examples.interactive
```

Choose `2` to call `set_value`, enter a dotted setting name, and enter its
value. Choose `3` to delete a setting, `4` to reload the file, or `5` to exit.
Changes made by the set and delete options are saved to `config.json`.

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
