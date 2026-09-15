# Normal Configuration vs FlegmCNF

This page compares a common plain-Python approach with FlegmCNF.

## 1. Read a JSON file

### Normal Python

```python
import json

with open("config.json", encoding="utf-8") as file:
    config = json.load(file)

app_name = config["app_name"]
port = config["database"]["port"]
```

### FlegmCNF

```python
from flegmcnf import Config

config = Config.from_file("config.json")

app_name = config["app_name"]
port = config["database.port"]
```

FlegmCNF uses dotted keys for nested values and creates the file if it does
not exist yet.

## 2. Use a default value

### Normal Python

```python
debug = config.get("debug", False)
port = config.get("database", {}).get("port", 5432)
```

### FlegmCNF

```python
debug = config.get("debug", False)
port = config.get("database.port", 5432)
```

## 3. Change and save a setting

### Normal Python

```python
config["debug"] = True
config["database"]["port"] = 5433

with open("config.json", "w", encoding="utf-8") as file:
    json.dump(config, file, indent=2)
```

### FlegmCNF

```python
config.set("debug", True)
config.set("database.port", 5433)
config.save("config.json")
```

FlegmCNF handles JSON formatting and creates missing folders for the output
file.

## 4. Require an important setting

### Normal Python

```python
if "secret_key" not in config:
    raise ValueError("Missing secret_key")

secret_key = config["secret_key"]
```

### FlegmCNF

```python
from flegmcnf import ConfigError

try:
    secret_key = config.require("secret_key")
except ConfigError:
    print("Missing secret_key")
```

## 5. Environment variable overrides

### Normal Python

```python
import os

if "APP_DEBUG" in os.environ:
    config["debug"] = os.environ["APP_DEBUG"].lower() == "true"

if "APP_DATABASE__HOST" in os.environ:
    config["database"]["host"] = os.environ["APP_DATABASE__HOST"]
```

### FlegmCNF

```python
config = Config.from_file("config.json", env_prefix="APP_")
```

The following variables are applied automatically:

```text
APP_DEBUG=true
APP_DATABASE__HOST=db.example.com
```

## Summary

| Task | Normal Python | FlegmCNF |
| --- | --- | --- |
| Read JSON | `json.load(file)` | `Config.from_file("config.json")` |
| Read nested value | `config["database"]["port"]` | `config["database.port"]` |
| Safe default | Manual nested `.get()` calls | `config.get("database.port", 5432)` |
| Change value | Direct dictionary edits | `config.set("database.port", 5433)` |
| Save JSON | `json.dump(...)` | `config.save("config.json")` |
| Required value | Manual check and exception | `config.require("secret_key")` |
| Environment overrides | Manual `os.environ` code | `env_prefix="APP_"` |
| Missing config file | Handle `FileNotFoundError` | Created automatically |
