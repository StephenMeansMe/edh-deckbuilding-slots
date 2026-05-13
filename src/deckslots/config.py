"""User configuration for deckslots."""

from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_config_dir


def get_config_path() -> Path:
    """Return the path to the user config file.

    Resolved via ``platformdirs`` so Windows and macOS get the native
    locations (``%APPDATA%`` and ``~/Library/Application Support``).
    On Linux this still honours ``$XDG_CONFIG_HOME``.
    """
    return Path(user_config_dir("deckslots", appauthor=False)) / "config.json"


def is_validation_enabled() -> bool:
    """Return True (default) unless the user config explicitly disables validation."""
    path = get_config_path()
    if not path.exists():
        return True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    return bool(data.get("validation_enabled", True))


def get_storage_backend() -> str:
    """Return the configured storage backend ('plaintext' or 'sqlite').

    Defaults to 'plaintext' when the config file is absent or malformed.
    Unknown values fall back to 'plaintext' too.
    """
    path = get_config_path()
    if not path.exists():
        return "plaintext"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "plaintext"
    value = str(data.get("storage_backend", "plaintext"))
    return value if value in ("plaintext", "sqlite") else "plaintext"
