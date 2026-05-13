"""Persistence layer for Decklists.

This module owns the storage seam (`DecklistRepository`) that the REPL,
the GUI, and future SQLite backend share. The plaintext format helpers
(`_format_save_file`, `_parse_save_file`) live here because they are
the on-disk format of the default `PlaintextRepository` backend; the
interop helpers `_format_export_file` / `_parse_import_file` stay in
`commands.py` because they are user-facing Moxfield/Archidekt encoders,
not storage.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import typing as _t
from typing import Protocol

from deckslots.exceptions import ParseError
from deckslots.models import (
    CappedCategory,
    Decklist,
    UncappedCategory,
)

_CARD_LINE_RE = re.compile(r"^(\d+)\s+(.+)$")
_SAVE_CAT_RE = re.compile(r"^(.+) \[(\d+) slots\]$")

# Single-deck backends (PlaintextRepository) always use this synthetic id.
_PLAINTEXT_DECK_ID = 1


def _get_save_path() -> Path:
    from platformdirs import user_state_dir

    return Path(user_state_dir("deckslots", appauthor=False)) / "decklist.bak"


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

    loaded_commander_cat = deck.categories.get("commander")
    if loaded_commander_cat is not None and isinstance(
        loaded_commander_cat, CappedCategory
    ):
        loaded_commander_cat.total_slots = max(1, len(loaded_commander_cat.cards))

    return deck


@dataclass(frozen=True)
class DecklistSummary:
    """Lightweight row returned by ``DecklistRepository.list``."""

    id: int
    name: str
    total_filled: int
    updated_at: str


class DecklistRepository(Protocol):
    """Storage seam shared by the plaintext and SQLite backends."""

    def save(self, deck: Decklist) -> int: ...

    def load(self, deck_id: int) -> Decklist: ...

    def load_by_name(self, name: str) -> Decklist | None: ...

    def list(self) -> list[DecklistSummary]: ...

    def delete(self, deck_id: int) -> None: ...


class PlaintextRepository:
    """Single-file backend writing to ``$XDG_STATE_HOME/deckslots/decklist.bak``.

    Implements :class:`DecklistRepository`. Because there is only ever one
    deck on disk, ``save`` always returns ``1`` and ``load`` ignores the
    ``deck_id`` argument (raising ``KeyError`` if the file is absent).
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else _get_save_path()

    def save(self, deck: Decklist) -> int:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(_format_save_file(deck))
        return _PLAINTEXT_DECK_ID

    def load(self, deck_id: int) -> Decklist:
        if not self._path.exists():
            raise KeyError(deck_id)
        return _parse_save_file(str(self._path))

    def load_by_name(self, name: str) -> Decklist | None:
        if not self._path.exists():
            return None
        deck = _parse_save_file(str(self._path))
        return deck if deck.name == name else None

    def list(self) -> list[DecklistSummary]:
        if not self._path.exists():
            return []
        # Surface parse failures via load(); list() must succeed so the REPL
        # can detect a present-but-corrupt save and offer recovery.
        try:
            deck = _parse_save_file(str(self._path))
            name, total_filled = deck.name, deck.total_filled
        except (ParseError, OSError, ValueError):
            name, total_filled = "?", 0
        mtime = self._path.stat().st_mtime
        updated_at = _dt.datetime.fromtimestamp(mtime, tz=_dt.timezone.utc).isoformat()
        return [
            DecklistSummary(
                id=_PLAINTEXT_DECK_ID,
                name=name,
                total_filled=total_filled,
                updated_at=updated_at,
            )
        ]

    def delete(self, deck_id: int) -> None:  # noqa: ARG002 - single-deck backend
        if self._path.exists():
            self._path.unlink()


# ---------------------------------------------------------------------------
# SqliteRepository
# ---------------------------------------------------------------------------


_SCHEMA_V1 = """
CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT);

CREATE TABLE decks (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  partners_enabled INTEGER NOT NULL DEFAULT 0,
  background_enabled INTEGER NOT NULL DEFAULT 0,
  companion_enabled INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE categories (
  id INTEGER PRIMARY KEY,
  deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('capped', 'uncapped')),
  fixed INTEGER NOT NULL,
  user_addable INTEGER NOT NULL,
  total_slots INTEGER,
  position INTEGER NOT NULL,
  UNIQUE (deck_id, name)
);

CREATE TABLE allowed_cards (
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  card_name TEXT NOT NULL,
  PRIMARY KEY (category_id, card_name)
);

CREATE TABLE cards (
  id INTEGER PRIMARY KEY,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  position INTEGER NOT NULL
);
CREATE INDEX cards_by_category ON cards (category_id, position);
"""

_SCHEMA_V2 = """
CREATE TABLE events (
  id         INTEGER PRIMARY KEY,
  deck_id    INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  payload    TEXT NOT NULL,
  applied_at TEXT NOT NULL
);
CREATE INDEX events_by_deck ON events (deck_id, id);
"""


def _get_db_path() -> Path:
    from platformdirs import user_data_dir

    return Path(user_data_dir("deckslots", appauthor=False)) / "library.db"


def _upgrade_to_v1(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_V1)


def _upgrade_to_v2(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_V2)


# Ordered list of (target_version, upgrade_fn). Append a new tuple to add a
# v3, v4, … migration. See docs/plans/2026-05-13-sqlite-migrations.md.
_MIGRATIONS: list[tuple[int, _t.Callable[[sqlite3.Connection], None]]] = [
    (1, _upgrade_to_v1),
    (2, _upgrade_to_v2),
]
CURRENT_SCHEMA_VERSION: int = _MIGRATIONS[-1][0]


def _current_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied schema version, or 0 if none recorded."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if row is None:
        return 0
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply pending schema upgrades in version order.

    Each upgrade is wrapped in a transaction (committed on success, rolled
    back on failure). A DB whose stored version exceeds
    ``CURRENT_SCHEMA_VERSION`` raises ``RuntimeError`` rather than risking
    silent corruption.
    """
    version = _current_version(conn)
    if version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {version} is newer than this app "
            f"supports ({CURRENT_SCHEMA_VERSION}). Please upgrade deckslots."
        )
    for target, upgrade_fn in _MIGRATIONS:
        if target <= version:
            continue
        try:
            upgrade_fn(conn)
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (target, _dt.datetime.now(tz=_dt.timezone.utc).isoformat()),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


class SqliteRepository:
    """Multi-deck backend backed by SQLite.

    Implements :class:`DecklistRepository`. The default database path is
    ``$XDG_DATA_HOME/deckslots/library.db``. Schema migrations run on every
    open via :func:`_migrate` and are idempotent.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path if path is not None else _get_db_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            _migrate(conn)
        self._maybe_import_legacy()

    def _maybe_import_legacy(self) -> None:
        """Seed an empty db from a legacy plaintext save, if present.

        First-run convenience for users opting into the SQLite backend who
        already have a deck on disk. The plaintext file is left in place
        as a read-only fallback.
        """
        if self.list():
            return
        legacy = _get_save_path()
        if not legacy.exists():
            return
        try:
            deck = _parse_save_file(str(legacy))
        except (ParseError, OSError, ValueError):
            return
        self.save(deck)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path))
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def save(self, deck: Decklist) -> int:
        now = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM decks WHERE name = ?", (deck.name,)
            ).fetchone()
            if row is not None:
                deck_id = row[0]
                conn.execute(
                    "UPDATE decks SET partners_enabled=?, background_enabled=?, "
                    "companion_enabled=?, updated_at=? WHERE id=?",
                    (
                        int(deck.partners_enabled),
                        int(deck.background_enabled),
                        int(deck.companion_enabled),
                        now,
                        deck_id,
                    ),
                )
                conn.execute("DELETE FROM categories WHERE deck_id=?", (deck_id,))
            else:
                cur = conn.execute(
                    "INSERT INTO decks (name, partners_enabled, background_enabled, "
                    "companion_enabled, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        deck.name,
                        int(deck.partners_enabled),
                        int(deck.background_enabled),
                        int(deck.companion_enabled),
                        now,
                        now,
                    ),
                )
                deck_id = cur.lastrowid
            for pos, cat in enumerate(deck.categories.values()):
                kind = "capped" if isinstance(cat, CappedCategory) else "uncapped"
                total_slots = (
                    cat.total_slots if isinstance(cat, CappedCategory) else None
                )
                cur = conn.execute(
                    "INSERT INTO categories (deck_id, name, kind, fixed, "
                    "user_addable, total_slots, position) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        deck_id,
                        cat.name,
                        kind,
                        int(cat.fixed),
                        int(cat.user_addable),
                        total_slots,
                        pos,
                    ),
                )
                cat_id = cur.lastrowid
                if cat.allowed_cards:
                    conn.executemany(
                        "INSERT INTO allowed_cards (category_id, card_name) "
                        "VALUES (?, ?)",
                        [(cat_id, c) for c in cat.allowed_cards],
                    )
                for cpos, card in enumerate(cat.cards):
                    conn.execute(
                        "INSERT INTO cards (category_id, name, position) "
                        "VALUES (?, ?, ?)",
                        (cat_id, card, cpos),
                    )
            conn.commit()
            return int(deck_id)

    def load(self, deck_id: int) -> Decklist:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT name, partners_enabled, background_enabled, "
                "companion_enabled FROM decks WHERE id=?",
                (deck_id,),
            ).fetchone()
            if row is None:
                raise KeyError(deck_id)
            name, partners, background, companion = row
            categories: dict[str, CappedCategory | UncappedCategory] = {}
            cat_rows = conn.execute(
                "SELECT id, name, kind, fixed, user_addable, total_slots "
                "FROM categories WHERE deck_id=? ORDER BY position",
                (deck_id,),
            ).fetchall()
            for cat_id, cname, kind, fixed, user_addable, total_slots in cat_rows:
                allowed_rows = conn.execute(
                    "SELECT card_name FROM allowed_cards WHERE category_id=?",
                    (cat_id,),
                ).fetchall()
                allowed = (
                    frozenset(r[0] for r in allowed_rows) if allowed_rows else None
                )
                card_rows = conn.execute(
                    "SELECT name FROM cards WHERE category_id=? ORDER BY position",
                    (cat_id,),
                ).fetchall()
                cards = [r[0] for r in card_rows]
                if kind == "capped":
                    cat: CappedCategory | UncappedCategory = CappedCategory(
                        name=cname,
                        total_slots=int(total_slots),
                        fixed=bool(fixed),
                        allowed_cards=allowed,
                        user_addable=bool(user_addable),
                        cards=cards,
                    )
                else:
                    cat = UncappedCategory(
                        name=cname,
                        fixed=bool(fixed),
                        allowed_cards=allowed,
                        user_addable=bool(user_addable),
                        cards=cards,
                    )
                categories[cname.lower()] = cat
        return Decklist(
            name=name,
            categories=categories,
            partners_enabled=bool(partners),
            background_enabled=bool(background),
            companion_enabled=bool(companion),
        )

    def load_by_name(self, name: str) -> Decklist | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM decks WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return None
        return self.load(int(row[0]))

    def list(self) -> list[DecklistSummary]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT d.id, d.name, d.updated_at, COUNT(c.id) AS total_filled "
                "FROM decks d "
                "LEFT JOIN categories cat ON cat.deck_id = d.id "
                "LEFT JOIN cards c ON c.category_id = cat.id "
                "GROUP BY d.id, d.name, d.updated_at "
                "ORDER BY d.updated_at DESC, d.id DESC"
            ).fetchall()
        return [
            DecklistSummary(
                id=int(r[0]), name=r[1], total_filled=int(r[3]), updated_at=r[2]
            )
            for r in rows
        ]

    def delete(self, deck_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
            conn.commit()

    # ------------------------------------------------------------------
    # Event log (Phase 3.3)
    # ------------------------------------------------------------------

    def append_event(self, deck_id: int, event: object) -> None:
        """Persist one DomainEvent to the events table."""
        import dataclasses
        import json

        payload = json.dumps(dataclasses.asdict(event))
        event_type = type(event).__name__
        now = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events (deck_id, event_type, payload, applied_at) "
                "VALUES (?, ?, ?, ?)",
                (deck_id, event_type, payload, now),
            )
            conn.commit()

    def load_events(
        self, deck_id: int, since_seq: int = 0
    ) -> list[tuple[int, object]]:
        """Return (id, DomainEvent) pairs for *deck_id* with id > since_seq."""
        import json

        from deckslots import events as ev_module

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, event_type, payload FROM events "
                "WHERE deck_id = ? AND id >= ? ORDER BY id",
                (deck_id, since_seq),
            ).fetchall()

        result = []
        for row_id, event_type, payload in rows:
            cls = getattr(ev_module, event_type, None)
            if cls is None:
                continue
            data = json.loads(payload)
            try:
                event = cls(**data)
            except TypeError:
                continue
            result.append((int(row_id), event))
        return result
