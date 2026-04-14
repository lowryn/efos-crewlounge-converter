import json
import os
from pathlib import Path
from config.defaults import DEFAULT_CONFIG


def _config_path() -> Path:
    # Always store in the user's home directory — writing inside a .app bundle
    # (Contents/MacOS/) can fail silently on macOS if the app is in /Applications.
    base = Path.home() / ".efos-converter"
    base.mkdir(parents=True, exist_ok=True)
    return base / "config.json"


def load() -> dict:
    path = _config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(saved)
            return config
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_CONFIG.copy()


def save(config: dict) -> None:
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
