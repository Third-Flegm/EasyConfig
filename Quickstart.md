# FlegmConfig quick start

Install FlegmConfig:

```powershell
python -m pip install flegmconfig
```

Create a `config.json` file:

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
print(config["database.host"])
config.set("debug", True)
config.save()
```

Useful commands:

```powershell
flegmconfig-docs --help
flegmconfig-docs --repo
flegmconfig-docs --quickstart
```

See `README.md` and `Syntax.md` for the complete documentation.
