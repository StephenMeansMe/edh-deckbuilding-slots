# Design: PySide6 GUI (Option B2)

Add a desktop GUI on top of the existing CLI/REPL using PySide6 (Qt for Python,
LGPL). The CLI stays the primary interface; the GUI is shipped as an opt-in
extra (`pip install deckslots[gui]`) and launched via `deckslots gui`.

## Goals

- Visual deck board: categories as drop targets, cards with art.
- Drag-and-drop between categories with full validation
  (allowed_cards, fullness, singleton exclusivity).
- Reuse the domain model and repository layer; no behaviour fork.

## Non-goals

- Replacing the REPL. The CLI keeps every command.
- Web/remote access. Single-process desktop app.
- Mobile/touch. Desktop-first.

## Prerequisite: service layer

The existing `handle_*` functions in `commands.py` mix domain mutation,
Scryfall validation, and string formatting. Extract a thin service layer first:

```python
# src/deckslots/services.py  (new)
@dataclass
class CommandResult:
    ok: bool
    message: str
    warnings: list[str]
    events: list[DomainEvent]

def add_card(deck: Decklist, card: str, category: str,
             scryfall_index: dict | None) -> CommandResult: ...
def move_card(deck: Decklist, card: str, to_category: str) -> CommandResult: ...
def can_drop(deck: Decklist, card: str, to_category: str) -> bool: ...   # GUI preflight
# ...one per user-facing operation
```

`DomainEvent` is an ADT (`CardAdded`, `CardMoved`, `CategoryCreated`, …) the
GUI consumes to refresh views without a full re-render. CLI handlers shrink to
a 2-3 line adapter that calls the service and stringifies the result.

## Architecture

```
src/deckslots/
├── services.py            # NEW — operations returning CommandResult
├── events.py              # NEW — DomainEvent ADT
└── gui/                   # NEW (loaded only when [gui] extra is installed)
    ├── __init__.py
    ├── app.py             # QApplication, main entry
    ├── main_window.py     # Deck board, menu bar
    ├── category_view.py   # QListView per category, drag/drop hooks
    ├── card_model.py      # QAbstractListModel wrapping a Category.cards list
    ├── card_inspector.py  # Right-pane card detail (image, type, legality)
    ├── deck_library.py    # Sidebar listing decks via repository.list()
    └── image_loader.py    # Async Scryfall image fetch + on-disk cache
```

`pyproject.toml` adds:
```toml
[project.optional-dependencies]
gui = ["PySide6>=6.6", "Pillow>=10.0"]
```

`cli.py` adds a `gui` subcommand:
```python
@click.command()
def gui():
    """Launch the deckslots GUI."""
    from deckslots.gui.app import run_app
    run_app()
```

## Drag-and-drop

- Each category is a `QListView` backed by `CardListModel(category)`.
- Drop targets implement `canDropMimeData` → `services.can_drop(deck, card, target)`.
- Illegal drop: red outline + tooltip with the rejection reason
  (matches existing exception messages: "category is full",
  "already in <category>", "card not allowed in this category").
- Legal drop: emits `services.move_card(...)`, the resulting `CardMoved` event
  triggers the source and target models to update.

## Card images

Extend `src/deckslots/scryfall.py`:

- `get_image_cache_dir() -> Path` → `$XDG_CACHE_HOME/deckslots/card_images/`.
- `fetch_card_image(name) -> Path` — uses `image_uris.normal` from the existing
  oracle_cards index when available; falls back to `GET /cards/named?fuzzy=`.
- Disk cache; in-memory `QPixmap` cache in `image_loader.py`.
- All network work happens off the GUI thread (`QThreadPool`); placeholder
  card-back image until the fetch lands. Respect Scryfall's 50–100 ms inter-request
  guidance.

## Wireframe

```
┌────────────────────────────────────────────────────────────────────────────┐
│ deckslots — Goldfish Fundamentals                      [Deck▾] [Tools▾] [?]│
├────────────────────────────────────────────────────────────────────────────┤
│ Slots: 87/100 ● Uncategorized: 3 ⚠   [Partner:off] [Background:off] [Companion:off]│
├──────────────────┬──────────────────┬──────────────────┬───────────────────┤
│ COMMANDER (1/1) █│ RAMP (10/10)   █│ REMOVAL (8/10)  ▓│ CARD ADVANTAGE    │
│  [card art]      │  [card] Sol Ring │  [card] Swords  │  (6/10)         ▒ │
│  Atraxa, …       │  [card] Arcane S │  [card] Path    │  [card] Rhystic   │
│                  │  [card] Nature's │  [card] Despark │  [card] Mystic R  │
├──────────────────┼──────────────────┼──────────────────┼───────────────────┤
│ BOARD WIPES (5/5)│ THREATS (15/15)█│ INTERACTION (4/5)│ UTILITY (3/5)   ▒ │
├──────────────────┴──────────────────┴──────────────────┴───────────────────┤
│ BASIC LANDS (uncapped: 34)   12× Island  10× Forest  8× Plains  4× Swamp   │
├────────────────────────────────────────────────────────────────────────────┤
│ UNCATEGORIZED ⚠ (3)   [card] Counterspell   [card] Cultivate   [card] D.T.│
└────────────────────────────────────────────────────────────────────────────┘
```

`█ = full (green) · ▓ = near full · ▒ = open slots · ⚠ = needs attention`

While dragging:
- Legal target: green outline + `✓` badge.
- Illegal target: red outline + tooltip with the exact rejection reason.
- Cursor reverts to source on `Esc` or invalid drop.

## Testing strategy

- **Service-layer contract** (`tests/test_services.py`): every service function
  has a unit test covering success, warnings, and rejection events. Existing
  `test_commands.py` tests are rewritten to drive the service layer.
- **GUI smoke** (`tests/gui/`): `pytest-qt` fixtures, drag/drop validation tests
  against `services.can_drop`. UI rendering tested only at the model boundary
  (model emits `dataChanged` after `CardMoved`).
- **Image loader**: integration test with a fake HTTP server confirms cache hit
  on second fetch.
- **CLI regression**: existing pytest + scrut suites pass unchanged after the
  service-layer refactor.

## Out of scope for v1

- Card search / typeahead (Phase 3).
- Undo/redo (Phase 3, requires DB-backed event log).
- Custom themes beyond Qt's default light/dark.
- Packaging as AppImage/dmg/exe (Phase 4).

## Critical files

- **New**: `src/deckslots/services.py`, `src/deckslots/events.py`,
  `src/deckslots/gui/*`, `tests/test_services.py`, `tests/gui/*`.
- **Modified**: `src/deckslots/commands.py` (handlers shrink to service
  adapters), `src/deckslots/scryfall.py` (image fetch + cache),
  `src/deckslots/cli.py` (`gui` subcommand), `pyproject.toml` (optional-deps).
