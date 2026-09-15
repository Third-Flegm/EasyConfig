# EasyConfig quick start

Install EasyConfig:

```powershell
python -m pip install easyconfig
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
from easyconfig import Config

config = Config.from_file("config.json")
print(config["database.host"])
config.set("debug", True)
config.save()
```

Useful commands:

```powershell
easyconfig-docs --help
easyconfig-docs --repo
easyconfig-docs --quickstart
```

See `README.md` and `Syntax.md` for the complete documentation.
