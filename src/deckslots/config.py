"""User configuration for deckslots."""

from __future__ import annotations

import json
import os
from pathlib import Path


def get_config_path() -> Path:
    """Return the path to the user config file."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        base = Path(xdg)
    else:
        base = Path.home() / ".config"
    return base / "deckslots" / "config.json"


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
