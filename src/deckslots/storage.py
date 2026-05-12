from __future__ import annotations

import os
import re
from collections import Counter
from pathlib import Path
from typing import Protocol

from deckslots.exceptions import ParseError
from deckslots.models import (
    CappedCategory,
    Decklist,
    UncappedCategory,
)

_CARD_LINE_RE = re.compile(r"^(\d+)\s+(.+)$")
_SAVE_CAT_RE = re.compile(r"^(.+) \[(\d+) slots\]$")


def _get_save_path() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME", "")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return base / "deckslots" / "decklist.bak"


def _format_save_file(decklist: Decklist) -> str:
    sections: list[str] = [f"# {decklist.name}"]
    for cat in decklist.categories.values():
        if cat.name == "Commander":
            heading = "Commander"
        elif cat.name == "Basic Lands":
            heading = "Basic Lands"
        elif cat.name == "Uncategorized":
            heading = "Uncategorized"
        elif cat.name == "Companion":
            heading = "Companion"
        else:
            assert isinstance(cat, CappedCategory)
            heading = f"{cat.name} [{cat.total_slots} slots]"
        lines = [heading]
        for card, qty in sorted(Counter(cat.cards).items()):
            lines.append(f"{qty} {card}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _parse_save_file(path: str) -> Decklist:
    try:
        with open(path) as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: '{path}'")

    stripped = [line.rstrip("\n") for line in lines]

    name: str | None = None
    start = 0
    for i, line in enumerate(stripped):
        if line.strip():
            if line.startswith("# "):
                name = line[2:].strip()
                start = i + 1
            break
    if name is None:
        raise ParseError("Save file missing '# <name>' header line.")

    deck = Decklist.create(name)
    # Temporarily expand Commander to accept any number of cards during load;
    # the correct slot count is set after all cards are read.
    commander_cat = deck.categories["commander"]
    assert isinstance(commander_cat, CappedCategory)
    commander_cat.total_slots = 99
    current_category: str | None = None

    for line in stripped[start:]:
        s = line.strip()
        if not s:
            continue
        if s == "Commander" or s.startswith("Commander ["):
            current_category = "Commander"
            continue
        if s == "Basic Lands":
            current_category = "Basic Lands"
            continue
        if s == "Uncategorized":
            if "uncategorized" not in deck.categories:
                deck.categories["uncategorized"] = UncappedCategory(
                    name="Uncategorized",
                    fixed=True,
                    user_addable=False,
                )
            current_category = "Uncategorized"
            continue
        if s == "Companion":
            deck.enable_companion()
            current_category = "Companion"
            continue
        m_cat = _SAVE_CAT_RE.match(s)
        if m_cat:
            cat_name = m_cat.group(1)
            slots = int(m_cat.group(2))
            deck.add_category(cat_name, slots)
            current_category = cat_name
            continue
        m_card = _CARD_LINE_RE.match(s)
        if m_card and current_category is not None:
            qty = int(m_card.group(1))
            card = m_card.group(2).strip()
            for _ in range(qty):
                deck.add_card(card, current_category)

    # Set Commander slot count from the number of loaded cards
    loaded_commander_cat = deck.categories.get("commander")
    if loaded_commander_cat is not None and isinstance(
        loaded_commander_cat, CappedCategory
    ):
        loaded_commander_cat.total_slots = max(1, len(loaded_commander_cat.cards))

    return deck


class DecklistRepository(Protocol):
    def save(self, deck: Decklist) -> None: ...
    def load(self) -> Decklist | None: ...
    def delete(self) -> None: ...


class PlaintextRepository:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else _get_save_path()

    def save(self, deck: Decklist) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(_format_save_file(deck))

    def load(self) -> Decklist | None:
        if not self._path.exists():
            return None
        return _parse_save_file(str(self._path))

    def delete(self) -> None:
        if self._path.exists():
            self._path.unlink()
