# Design: SQLite as Default Backend for the GUI

The GUI (`deckslots gui`) should always use `SqliteRepository` regardless of the
`storage_backend` setting in `config.json`. The multi-deck workflow — deck library
panel, switching, deleting — is the *only* workflow the GUI offers; it makes no
sense to open the GUI and land on a single-file `PlaintextRepository` that shows
no deck library panel and has no deck-switching affordance.

The REPL path is unchanged: it continues to honour `config.get_storage_backend()`
and defaults to `"plaintext"`.

## Goals

- `deckslots gui` always uses `SqliteRepository`, with no config.json required.
- A user coming from the REPL with a `decklist.bak` gets their deck auto-imported
  into the database on first GUI launch (already handled by `_maybe_import_legacy()`).
- CLI / REPL users are unaffected — their default stays `PlaintextRepository`.

## Non-goals

- Removing the `storage_backend` config key. The REPL still respects it.
- Showing a backend-picker dialog. The GUI always uses SQLite.

## Design

### `src/deckslots/gui/app.py`

Replace the current backend selection in `run_app()`:

```python
# Before (reads config, may return PlaintextRepository):
repo = _pick_repository()

# After (always SQLite for the GUI):
from deckslots.storage import SqliteRepository
repo = SqliteRepository()
```

`SqliteRepository.__init__` already calls `_maybe_import_legacy()`, which seeds the
database from any existing `decklist.bak` exactly once (when the DB is empty). No
additional migration code is needed.

### First-launch experience

| Scenario | Result |
|----------|--------|
| Brand-new install, no `decklist.bak` | Empty library; `run_app()` creates a `"New Deck"` as before |
| Existing `decklist.bak`, no `library.db` | `_maybe_import_legacy()` imports the deck; user sees it in the library panel |
| Existing `library.db` already | Normal open; legacy import is a no-op |

## Testing strategy

- **Unit** (`tests/gui/test_app.py`): patch `SqliteRepository` and assert `run_app()`
  constructs it without reading `config.get_storage_backend()`.
- **Integration**: run `deckslots gui` from a clean XDG temp directory containing
  only a `decklist.bak`; assert `library.db` is created and the imported deck loads.

## Backwards compatibility

REPL users (`deckslots` with no subcommand) are unaffected. The `storage_backend`
config key retains its meaning for the REPL. GUI users who previously set
`{"storage_backend": "plaintext"}` to force plaintext in the GUI will now always
get SQLite; this is intentional — the plaintext backend cannot support the GUI deck
library panel.

## Critical files

- **Modified**: `src/deckslots/gui/app.py` (remove `_pick_repository()` call, hard-code `SqliteRepository`)
- **Tests**: `tests/gui/test_app.py`
