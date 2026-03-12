"""Template model and I/O for deckslots category templates."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from importlib.resources import files as resource_files
from pathlib import Path

from deckslots.exceptions import ParseError

_TMPL_CAT_RE = re.compile(r"^(.+) \[(\d+) slots\]$")


@dataclass
class Template:
    name: str
    categories: list[tuple[str, int]]
    builtin: bool = False


def _load_builtin_templates() -> list[Template]:
    """Load all built-in templates shipped with the package."""
    templates: list[Template] = []
    data_dir = resource_files("deckslots").joinpath("data/templates")
    for entry in data_dir.iterdir():  # type: ignore[union-attr]
        if entry.name.endswith(".tmpl"):
            content = entry.read_text("utf-8")
            t = _parse_template_content(content)
            t.builtin = True
            templates.append(t)
    return sorted(templates, key=lambda t: t.name)


def load_all_templates() -> list[Template]:
    """Return all templates (built-in + user), sorted by name."""
    templates: list[Template] = list(_load_builtin_templates())
    user_dir = _get_user_template_dir()
    if user_dir.exists():
        for path in sorted(user_dir.glob("*.tmpl")):
            try:
                content = path.read_text("utf-8")
                t = _parse_template_content(content)
                t.builtin = False
                templates.append(t)
            except Exception:
                pass  # skip malformed user templates silently
    return sorted(templates, key=lambda t: t.name)


def find_template(name: str) -> Template | None:
    """Look up a template by exact name across all templates."""
    for t in load_all_templates():
        if t.name == name:
            return t
    return None


def _get_user_template_dir() -> Path:
    """Return the XDG-compliant user template directory."""
    data_home = os.environ.get("XDG_DATA_HOME", "")
    base = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base / "deckslots" / "templates"


def _format_template(template: Template) -> str:
    """Serialise a Template to its plain-text file format."""
    lines = [f"# {template.name}"]
    for cat_name, slots in template.categories:
        lines.append(f"{cat_name} [{slots} slots]")
    return "\n".join(lines) + "\n"


def _parse_template_content(text: str) -> Template:
    """Deserialise a template from plain-text content. Raises ParseError on bad input."""
    lines = [line.rstrip("\n") for line in text.splitlines()]
    name: str | None = None
    categories: list[tuple[str, int]] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            name = stripped[2:].strip()
            continue
        m = _TMPL_CAT_RE.match(stripped)
        if m:
            categories.append((m.group(1), int(m.group(2))))

    if name is None:
        raise ParseError("Template file missing '# <name>' header line.")

    return Template(name=name, categories=categories)
