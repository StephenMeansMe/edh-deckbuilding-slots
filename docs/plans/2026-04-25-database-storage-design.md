# Design: Database-Backed Storage (Option A1)

Replace the single-file plain-text save (`$XDG_STATE_HOME/deckslots/decklist.bak`)
with a SQLite database at `$XDG_DATA_HOME/deckslots/library.db`, using only the
stdlib `sqlite3` module. Plaintext `decklist import` / `decklist export` keep
their Moxfield/Archidekt-compatible semantics unchanged.

## Goals

- Persist multiple decks (deck library) instead of one `decklist.bak`.
- Persist mode flags (`partners_enabled`, `background_enabled`, `companion_enabled`)
  explicitly rather than inferring from Commander card count.
- Introduce a storage seam (`DecklistRepository`) that the GUI can reuse.
- Zero new runtime dependencies.

## Non-goals

- Replacing plaintext `import` / `export`. Those are user-facing interop and stay.
- Cross-deck queries beyond `list()`. Tagging, search, and history are deferred.
- Concurrency. Single-process assumption; no file locking.

## Schema (`schema_version = 1`)

```sql
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
  total_slots INTEGER,                    -- NULL for uncapped
  position INTEGER NOT NULL,              -- preserves insertion order
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
  position INTEGER NOT NULL                -- preserves list[str] order
);
CREATE INDEX cards_by_category ON cards (category_id, position);
```

`PRAGMA foreign_keys = ON` is enabled per connection. Migrations are hand-rolled
in `storage.py`: a single `_migrate(conn)` function reads `schema_version` and
applies each upgrade in order.

## Architecture

### New module: `src/deckslots/storage.py`

```python
class DecklistRepository(Protocol):
    def save(self, deck: Decklist) -> int: ...           # returns deck id
    def load(self, deck_id: int) -> Decklist: ...
    def load_by_name(self, name: str) -> Decklist | None: ...
    def list(self) -> list[DecklistSummary]: ...
    def delete(self, deck_id: int) -> None: ...

class PlaintextRepository(DecklistRepository): ...       # wraps existing _format_/_parse_save_file
class SqliteRepository(DecklistRepository): ...          # new
```

`DecklistSummary` is `(id: int, name: str, total_filled: int, updated_at: str)`.

### Migration on first run

When `storage_backend = "sqlite"` is enabled and `library.db` does not exist:
1. Create schema, write `schema_version = 1`.
2. If a legacy `$XDG_STATE_HOME/deckslots/decklist.bak` exists, parse it via
   `_parse_save_file` and `save()` it as the first deck. Leave the legacy file
   in place (read-only fallback).

### Wiring

- `Session` (`commands.py:44–47`) gains `repository: DecklistRepository`.
- `handle_decklist_save` / `handle_decklist_load` (`commands.py:592–614`) call
  `session.repository.save(...)` / `.load_by_name(...)`.
- `_format_save_file` / `_parse_save_file` move into `PlaintextRepository`
  unchanged; `_format_export_file` / `_parse_import_file` stay in `commands.py`
  (interop, not storage).
- `config.py` adds `storage_backend: "plaintext" | "sqlite"`, default `"plaintext"`.
- `repl.py:81–115` selects the repo from config at startup.

### New CLI affordances (Phase 1.3)

| Command | Description |
|---|---|
| `decklist list` | List decks in the library (id, name, total filled, updated_at) |
| `decklist switch <name>` | Replace `Session.decklist` with the named deck |
| `decklist delete <name>` | Remove a deck from the library (prompt to confirm) |

## Testing strategy

- **Repository contract** (`tests/test_storage_repository.py`): parametrized
  over `PlaintextRepository` and `SqliteRepository`. Round-trips every fixed-mode
  combination (none, partner, background, partner+background, companion +
  each), asserting `Decklist` model equality after save→load.
- **Schema migration**: test that opening a fresh DB applies version 1; opening
  an already-migrated DB is a no-op.
- **Legacy import**: fixture `decklist.bak` files load into SQLite and produce
  byte-identical plaintext export.
- **scrut**: existing functional suite must pass unchanged with default
  `storage_backend = "plaintext"`; an additional functional run with
  `storage_backend = "sqlite"` (env var override) covers save/load/list/switch.

## Backwards compatibility

- Default backend stays `"plaintext"`. Existing users see no change.
- `storage_backend = "sqlite"` is opt-in via `config.json`.
- Plaintext `decklist save <file>` / `decklist load <file>` continue to work
  against arbitrary file paths regardless of backend (escape hatch).

## Critical files

- **New**: `src/deckslots/storage.py`, `tests/test_storage_repository.py`
- **Modified**: `src/deckslots/commands.py` (Session, save/load handlers,
  extract `_format_save_file`/`_parse_save_file` into `PlaintextRepository`),
  `src/deckslots/repl.py` (startup chooses repo), `src/deckslots/config.py`
  (storage_backend setting).
