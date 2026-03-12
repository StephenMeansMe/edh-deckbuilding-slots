"""Template model and I/O for deckslots category templates."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Template:
    name: str
    categories: list[tuple[str, int]]
    builtin: bool = False
