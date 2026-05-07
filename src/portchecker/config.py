"""Configuration management for Port Checker."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Config paths
CONFIG_DIR = Path.home() / ".config" / "portchecker"
CONFIG_FILE = CONFIG_DIR / "config.json"
FAVORITES_FILE = CONFIG_DIR / "favorites.json"


def ensure_config_dir() -> None:
    """Ensure configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def load_favorites() -> List[Dict]:
    """Load favorite ports from file."""
    if FAVORITES_FILE.exists():
        try:
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("favorites", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_favorites(favs: List[Dict]) -> None:
    """Save favorite ports to file."""
    ensure_config_dir()
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump({"favorites": favs}, f, indent=2)


def add_favorite(port: int, name: str, note: str = "") -> bool:
    """Add a favorite port. Returns False if port already exists."""
    favs = load_favorites()
    for f in favs:
        if f['port'] == port:
            return False
    favs.append({'port': port, 'name': name, 'note': note})
    save_favorites(favs)
    return True


def remove_favorite(identifier: str) -> bool:
    """Remove a favorite by port number or name. Returns True if found."""
    favs = load_favorites()
    for i, f in enumerate(favs):
        if str(f['port']) == identifier or f['name'].lower() == identifier.lower():
            favs.pop(i)
            save_favorites(favs)
            return True
    return False


def get_favorite_by_name(name: str) -> Dict | None:
    """Get a favorite by name (case-insensitive)."""
    favs = load_favorites()
    return next((f for f in favs if f['name'].lower() == name.lower()), None)


def get_cli_path() -> str | None:
    """Get the configured CLI path from environment or config."""
    # Check environment first
    env_path = os.environ.get("PORTCHECKER_CLI", "").strip()
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    # Check config
    config = load_config()
    config_path = config.get("cli_path", "").strip()
    if config_path and os.path.isfile(config_path) and os.access(config_path, os.X_OK):
        return config_path

    return None
