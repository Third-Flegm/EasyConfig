# EasyConfig

EasyConfig makes it easy to store application settings in a separate
`config.json` file.

## Quick start

Install the package, then create a `config.json` file:

```json
{
    "app_name": "my-service",
    "debug": false,
    "database": {
        "host": "localhost",
        "port": 5432
    }
}
```

Load and use it in Python:

```python
from easyconfig import Config

config = Config.from_file("config.json")

print(config["app_name"])
print(config["database.host"])

config.set("debug", True)
config.save("config.json")
```

If `config.json` does not exist yet, `Config.from_file` creates it with an
empty configuration so you can start adding values with `set`.

Run the example from the project root with `python -m examples.basic`.

For the complete reference, see [Syntax.md](Syntax.md). To compare EasyConfig
with regular Python dictionaries and the `json` module, see [Compare.md](Compare.md).

## Optional environment overrides

Environment variables can override values without changing `config.json`.
Pass a prefix when loading the file:

```python
config = Config.from_file("config.json", env_prefix="APP_")
```

These variables then override the file values:

```text
APP_DEBUG=true
APP_DATABASE__HOST=db.example.com
```

Double underscores represent nested keys. JSON and TOML files are supported.
