# FlegmConfig

FlegmConfig makes it easy to store application settings in a separate
`config.json` file.

## Installation

Install the package from PyPI when published:

```powershell
python -m pip install flegmconfig
```

For local development, install the current project in editable mode:

```powershell
python -m pip install -e .
```

The [pyproject.example.toml](pyproject.example.toml) file shows the minimum
metadata for a project that depends on FlegmConfig.

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
from flegmconfig import Config

config = Config.from_file("config.json")

print(config["app_name"])
print(config["database.host"])

config.set("debug", True)
config.save("config.json")
```

If `config.json` does not exist yet, `Config.from_file` creates it with an
empty configuration so you can start adding values with `set`. Relative paths
are created beside the Python file that called `from_file`, not beside the
terminal's current working directory.

Run the example from the project root with `python -m examples.basic`.

For a menu-driven example, run `python -m examples.interactive`. It offers:

1. Show settings
2. Set a setting, using names such as `database.port`
3. Delete a setting
4. Reload settings from `config.json`
5. Exit

The set and delete options save changes to the file. Values such as `true`,
`42`, and `3.14` are read as JSON values; other input is stored as text.

For the complete reference, see [Syntax.md](Syntax.md). To compare FlegmConfig
with regular Python dictionaries and the `json` module, see [Compare.md](Compare.md).

## Optional environment overrides

Environment variables can override values at runtime without changing
`config.json`. Calling `save()` never writes environment-only overrides back
to the file.
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

## Package user quick start

If you install FlegmConfig from PyPI or a local wheel, you can start with:

```python
from flegmconfig import Config

config = Config.from_file("config.json")
config.setdefault("database.port", 5432)
config.update({"debug": True})
```

The library keeps nested settings easy to read with dotted keys like
`database.port`, while still supporting full JSON/TOML loading.

## Additional API

The complete API is documented in [Syntax.md](Syntax.md). It includes
`delete`, `reload`, `to_dict`, type schemas, `update`, `setdefault`, and the
`MISSING` sentinel for distinguishing an absent setting from a setting whose
value is `null`.

## Merge and defaults

You can merge mappings and set defaults without losing nested values:

```python
config = Config({"database": {"host": "localhost", "port": 5432}})
config.update({"database": {"port": 5433}, "debug": True})
config.setdefault("database.user", "app")
```

`update` accepts dotted keys and nested dictionaries. `setdefault` only sets a
value when the key is missing.

## Install the bundled docs

After installing the package, you can copy the bundled documentation files into
any directory with:

```powershell
flegmconfig-docs
```

The command places `README.md` and `Syntax.md` in the installed package's parent
folder by default, which makes it easy to browse the docs alongside the library.
Existing files are left alone unless `--force` is supplied. The same command also
provides project helpers:

```powershell
flegmconfig-docs --help
flegmconfig-docs --quickstart
flegmconfig-docs --repo
flegmconfig-docs --version
```

`--quickstart` writes a small `QUICKSTART.md` guide to the current directory.
Add a directory after the command to write there instead, for example
`flegmconfig-docs --quickstart .\docs`.
You can also call it from Python:

```python
from flegmconfig import install_docs

install_docs("./docs")
```

## TOML support

On Python 3.11 and newer, TOML reading uses the standard-library `tomllib` and
needs no extra package. On Python 3.10, FlegmConfig installs and uses the
backport `tomli`. FlegmConfig reads TOML but `save()` always writes JSON, so no
`tomli-w` dependency is needed.
