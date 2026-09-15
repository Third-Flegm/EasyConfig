"""A beginner-friendly interactive EasyConfig example.

Run from the project root:
    python -m examples.interactive
"""

import json

from easyconfig import MISSING, Config, ConfigError


CONFIG_FILE = "config.json"


def set_value(config: Config) -> None:
    """Ask for a setting and save the new value."""
    key = input("Setting name (for example database.port): ").strip()
    raw_value = input("Value: ").strip()
    if not key:
        print("The setting name cannot be empty.")
        return

    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        value = raw_value

    config.set(key, value)
    config.save(CONFIG_FILE)
    print("Saved.")


def show_values(config: Config) -> None:
    print(json.dumps(config.to_dict(), indent=2, sort_keys=True))


def main() -> None:
    config = Config.from_file(CONFIG_FILE)
    if config.get("app.name", MISSING) is MISSING:
        config.set("app.name", "my-service")
        config.set("debug", False)
        config.save(CONFIG_FILE)

    while True:
        print("\nEasyConfig")
        print("1. Show settings")
        print("2. Set a setting")
        print("3. Delete a setting")
        print("4. Reload from disk")
        print("5. Exit")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                show_values(config)
            elif choice == "2":
                set_value(config)
            elif choice == "3":
                key = input("Setting name to delete: ").strip()
                print("Deleted." if config.delete(key) else "Setting not found.")
                config.save(CONFIG_FILE)
            elif choice == "4":
                config.reload()
                print("Reloaded.")
            elif choice == "5":
                print("Goodbye.")
                return
            else:
                print("Please choose a number from 1 to 5.")
        except ConfigError as error:
            print(f"Configuration problem: {error}")


if __name__ == "__main__":
    main()
