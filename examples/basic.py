"""Basic EasyConfig usage example.

Run from the project root:
    python -m examples.basic

Try an override:
    APP_DEBUG=true APP_DATABASE__HOST=db.example.com python -m examples.basic
"""

from easyconfig import MISSING, Config


config = Config.from_file("config.json", env_prefix="APP_")

if config.get("app.name", MISSING) is MISSING:
    config.set("app.name", "my-service")
    config.set("debug", False)
    config.set("database.host", "localhost")
    config.set("database.port", 5432)
    config.save("config.json")

# Read values from config.json.
print(f"Service: {config.require('app.name')}")
print(f"Debug: {config['debug']}")
print(f"Database: {config['database.host']}:{config['database.port']}")

# To change and save a value, use these two lines:
# config.set("debug", True)
# config.save("config.json")
