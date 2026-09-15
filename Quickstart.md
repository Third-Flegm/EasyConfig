# FlegmCNF quick start

Install FlegmCNF:

```powershell
python -m pip install flegmcnf
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
from flegmcnf import Config

config = Config.from_file("config.json")
print(config["database.host"])
config.set("debug", True)
config.save()
```

Useful commands:

```powershell
flegmcnf --help
flegmcnf --repo
flegmcnf --quickstart
```

See `README.md` and `Syntax.md` for the complete documentation.
