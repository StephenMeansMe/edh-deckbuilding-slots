# Architecture

The app uses an **object-verb command pattern** with a dispatch registry.

> **GUI work?** The target design is in [`docs/design/design-handoff.md`](../../docs/design/design-handoff.md). Read that before implementing Phase 2. The hi-fi prototype (`docs/design/Big Bridge Energy.html`) is the visual target — open it in a browser.

## Module Layout

CLI-facing modules live in the `cli/` subpackage; the top of `deckslots/` holds the domain model, services, persistence, and shared infrastructure.

```
src/deckslots/
├── cli/                # CLI/REPL layer
│   ├── __init__.py     # re-exports ParsedCommand, parse_command, main
│   ├── parser.py       # ParsedCommand + parse_command + main (entry point)
│   ├── commands.py     # Session, handlers, dispatch registry
│   ├── repl.py         # run_repl loop
│   └── status.py       # render_status_line
├── models.py           # Decklist, Category, BASIC_LAND_NAMES
├── services.py         # Pure domain functions → CommandResult
├── events.py           # DomainEvent ADT
├── storage.py          # DecklistRepository + PlaintextRepository
├── templates.py        # Template, load/save/import/export
├── scryfall.py         # Card-name validation index
├── config.py           # config.json reader
├── logging_config.py   # File logging setup
└── exceptions.py       # DecklistError hierarchy
```

`pyproject.toml` keeps its `deckslots = "deckslots.cli:main"` entry point — `main` is re-exported from `cli/__init__.py`.

## cli/parser.py

- `parse_command(line)` returns a `ParsedCommand`
- `ParsedCommand` fields: `kind` (`builtin`, `object_verb`, `unknown`, `empty`), `obj`, `verb`, `args`, `raw`, `builtin`
- Known objects: `decklist`, `category`, `card`, `template`
- Builtins: `quit`, `exit`, `help`
- `main()` — console-script entry point (sets up logging, calls `run_repl`)

## models.py

- `Category` is an **abstract base class** with two concrete subclasses:
  - `CappedCategory(name, total_slots, fixed, allowed_cards, user_addable, cards)` — fixed upper bound (1–99 slots); `available` returns remaining slots; `is_full` returns True when full
  - `UncappedCategory(name, fixed, allowed_cards, user_addable, cards)` — no upper bound; `available` returns None; `is_full` always False
- `Decklist` fields: `name`, `categories: dict[str, Category]` (keyed by lowercase name), `partners_enabled`, `background_enabled`, `companion_enabled`
- `Decklist.create()` — factory that auto-creates Commander (CappedCategory, 1 slot, fixed) and Basic Lands (UncappedCategory, fixed, allowed_cards=BASIC_LAND_NAMES)
- `Decklist.add_card(card, category_name)` — enforces: category existence, `allowed_cards` whitelist, fullness, singleton exclusivity across all CappedCategory instances (uncapped categories skip exclusivity)
- `Decklist.find_card(card)` — returns the category key containing the card, or None
- `Decklist.move_card(card, to_category_name)` — validates target, then atomically removes from source and appends to target; does NOT call `add_card` internally (avoids spurious exclusivity failure)
- `Decklist.apply_template(template)` — replaces all user-created categories with the template's categories; displaced cards move to Uncategorized
- Mode methods — each expands or contracts `Commander.total_slots` by 1; disable methods evacuate Commander cards to Uncategorized:
  - `enable_partners()` / `disable_partners()`
  - `enable_background()` / `disable_background()`
  - `enable_companion()` / `disable_companion()` — creates/removes a separate `CappedCategory("Companion", 1, fixed=True)`; does not affect Commander slot count
- Computed properties: `total_slots` (sum of CappedCategory.total_slots), `total_filled`, `commander_overcrowded` (Commander has more cards than enabled modes allow), `companion_slot_empty` (Companion enabled but no card added)
- `BASIC_LAND_NAMES` — module-level `frozenset[str]` of all 12 valid basic land names (Plains through Snow-Covered Wastes)

## events.py (Phase 0+)

`DomainEvent` ADT — a union of frozen dataclasses representing state mutations. Used by the GUI (Phase 2) to refresh only changed views.

- `CardAdded(card, category)`, `CardMoved(card, from_category, to_category)`, `CardRemoved(card, from_category)`, `CardDeleted(card, from_category)`
- `CategoryCreated(name, slots)`, `CategoryResized(name, old_slots, new_slots)`, `CategoryDeleted(name, cards_displaced)`, `CategoryRenamed(old_name, new_name)`
- `DecklistRenamed(old_name, new_name)`
- `ModeEnabled(mode)`, `ModeDisabled(mode)` — mode is `"partners"`, `"background"`, or `"companion"`
- `TemplateApplied(template_name, cards_displaced)`

## services.py (Phase 0+)

Pure domain functions — accept a `Decklist`, return a `CommandResult`. No I/O. Called by REPL handlers (thin adapters) and directly by the GUI.

```python
@dataclass
class CommandResult:
    ok: bool
    message: str
    warnings: list[str]    # e.g. Scryfall "not found" warnings
    events: list[DomainEvent]
```

Functions: `add_card`, `move_card`, `can_drop` (preflight predicate, returns `bool`), `remove_card`, `delete_card`, `create_category`, `resize_category`, `delete_category`, `rename_category`, `rename_decklist`, `enable_partners`, `disable_partners`, `enable_background`, `disable_background`, `enable_companion`, `disable_companion`, `apply_template`.

## storage.py (Phase 1+)

Persistence layer that owns the storage seam.

- `DecklistRepository` (Protocol) — 5 methods: `save(deck) -> int`, `load(deck_id) -> Decklist`, `load_by_name(name) -> Decklist | None`, `list() -> list[DecklistSummary]`, `delete(deck_id) -> None`
- `DecklistSummary` — frozen dataclass `(id: int, name: str, total_filled: int, updated_at: str)` returned by `list()`
- `PlaintextRepository(path=None)` — single-file backend at `$XDG_STATE_HOME/deckslots/decklist.bak`. Implements the protocol with a synthetic ID of 1; `list()` returns one summary if the file exists (tolerating parse errors so the REPL can detect corruption via `load()`).
- `SqliteRepository(path=None)` — multi-deck backend at `$XDG_DATA_HOME/deckslots/library.db` (stdlib `sqlite3`, `PRAGMA foreign_keys = ON`). Schema migrations in `_migrate(conn)`; currently `schema_version = 1`. `save()` upserts by deck name; `_maybe_import_legacy()` seeds an empty db from any existing `decklist.bak`.
- `_format_save_file(decklist)` / `_parse_save_file(path)` / `_get_save_path()` — plain-text format helpers (private; used by both repository implementations)

## cli/commands.py

- `Session` holds REPL state: `decklist: Decklist | None`, `scryfall_index: dict | None`, `repository: DecklistRepository` (default-constructed `PlaintextRepository`)
- Handler functions (e.g., `handle_decklist_create`) return strings; domain handlers are thin adapters that call `services.*` and format the result
- I/O helpers:
  - Storage round-trip (`_format_save_file`, `_parse_save_file`, `_get_save_path`) lives in `storage.py` and is re-exported from `commands.py` for backward compatibility
  - `_format_export_file(decklist)` / `_parse_import_file(path)` — Moxfield/Archidekt-compatible format (interop, stays in `commands.py`)
- Multi-deck handlers route through `session.repository` (`handle_decklist_save/load/list/switch/delete`); `decklist delete` prompts via `click.confirm`
- `_resolve_category_and_card(args, categories)` — greedy longest-prefix match for `<category> <card>` args (used by `card add`)
- `_resolve_card_and_category_suffix(args, categories)` — greedy longest-suffix match for `<card> <category>` args (used by `card move`)
- `register_all_handlers(session)` — builds `dict[tuple[str, str], Callable]` dispatch registry covering decklist, category, card, and template handlers
- `dispatch(cmd, registry)` — routes commands to the appropriate handler

## cli/repl.py

- `run_repl()` — creates a Session and registry, then loops on `input()`:
  - On startup, loads/resumes the last saved decklist from XDG state home
  - Prompts once for Scryfall index download (on first run or if cache is stale > 7 days)
  - Parses each line with `parse_command`, dispatches to handlers via `dispatch`
  - After every command, injects persistent warnings (via `click.echo`) when:
    - Uncategorized is non-empty
    - `commander_overcrowded` is True
    - `companion_slot_empty` is True
  - Catches EOFError / KeyboardInterrupt for graceful exit
- Uses `click.echo` for output and `click.prompt` for interactive rename/download prompts

## scryfall.py

- `build_name_index(cards)` — creates lowercase-name → card dict; handles DFC/split cards by indexing all face names
- `validate_card(card_name, index)` → `ValidationResult(card, found, commander_legal)`
- `get_cache_path()` — XDG-compliant cache path (`$XDG_CACHE_HOME/deckslots/oracle_cards.json`)
- `is_cache_stale(path, max_age_days=7)` — checks file age
- `load_index_from_cache(path)` → index dict or None
- `fetch_bulk_data_url()` — queries Scryfall API for the oracle_cards bulk download URI
- `download_oracle_cards(dest)` — fetches and writes bulk data to cache

## templates.py

- `Template` — dataclass: `name: str`, `categories: list[tuple[str, int]]`, `builtin: bool`
- `_load_builtin_templates()` — loads `.tmpl` files from `src/deckslots/data/templates/`
- `load_all_templates()` — returns built-in + user templates, sorted by name
- `find_template(name)` → Template | None (case-insensitive)
- `save_user_template(template)` — writes to `$XDG_DATA_HOME/deckslots/templates/`
- `user_template_exists(name)` → bool
- `_format_template(template)` / `_parse_template_content(text)` — plain-text round-trip (`# <name>` header, then `<name> [<n> slots]` lines)

## config.py

- `get_config_path()` → XDG-compliant path (`$XDG_CONFIG_HOME/deckslots/config.json`)
- `is_validation_enabled()` → bool — reads `config.json`; defaults to True if absent
- `get_storage_backend()` → `"plaintext"` (default) or `"sqlite"`; reads `config.json`; falls back to `"plaintext"` on missing/malformed config or unknown value

## storage.py

Persistence layer that owns the storage seam.

- `DecklistRepository` (Protocol) — 5 methods: `save(deck) -> int`, `load(deck_id) -> Decklist`, `load_by_name(name) -> Decklist | None`, `list() -> list[DecklistSummary]`, `delete(deck_id) -> None`
- `DecklistSummary` — frozen dataclass `(id: int, name: str, total_filled: int, updated_at: str)` returned by `list()`
- `PlaintextRepository(path=None)` — single-file backend at `$XDG_STATE_HOME/deckslots/decklist.bak`. Implements the protocol with a synthetic ID of 1; `load()` ignores `deck_id` and `delete()` removes the file. `list()` returns one summary if the file exists (or `[]` otherwise), tolerating parse errors so the REPL can detect corruption via `load()`.
- `SqliteRepository(path=None)` — multi-deck backend at `$XDG_DATA_HOME/deckslots/library.db` (stdlib `sqlite3`, `PRAGMA foreign_keys = ON`). Schema migrations are hand-rolled in `_migrate(conn)` — currently `schema_version = 1` with `decks`, `categories`, `allowed_cards`, `cards` tables (cards table has a `cards_by_category` index on `(category_id, position)`). `save()` upserts by deck name; `_maybe_import_legacy()` runs once on the first open of an empty db to seed it from any existing `decklist.bak` (the plaintext file is preserved as a read-only fallback).
- `_format_save_file(decklist)` / `_parse_save_file(path)` / `_get_save_path()` — plain-text format helpers (private; used by both `PlaintextRepository` and the legacy import path)

## exceptions.py

Custom exception hierarchy used throughout the codebase:

```
DecklistError
├── CardError
├── SlotError
├── CategoryError
├── FileError
└── ParseError
```

## logging_config.py

- `setup_logging(debug: bool)` — configures file-based debug logging to `$XDG_DATA_HOME/deckslots/debug.log`
- Only active when the `--debug` flag is passed to the CLI

---

## Command Grammar

All commands follow `<object> <verb> [arguments...]`.

### `decklist` commands

| Command | Description |
|---|---|
| `decklist create <name>` | Create a new decklist; auto-creates `Commander` (1 fixed slot) and `Basic Lands` (uncapped, basic lands only) categories |
| `decklist show` | Print summary: decklist name, each category with filled/total slots, grand total |
| `decklist rename <new-name>` | Rename the current decklist |
| `decklist export <filename>` | Export to Moxfield/Archidekt-compatible plain text file (Commander, optional Companion, Maindeck sections) |
| `decklist save <filename>` | Save decklist structure to a file (categories, slots, cards) |
| `decklist load <filename>` | Load decklist structure from a file |
| `decklist list` | List all decks in the library (id, name, card count, last-updated date) |
| `decklist switch <name>` | Replace the active deck with a saved deck by name |
| `decklist delete <name>` | Remove a saved deck from the library (prompts to confirm) |
| `decklist import <filename>` | Import a plain-text decklist (Commander/Companion/Maindeck headings); routes cards to Commander slot, Basic Lands, and Uncategorized |
| `decklist enable-partner` | Expand Commander slot to 2 for the partner mechanic |
| `decklist disable-partner` | Revert Commander to 1 slot; all Commander cards move to Uncategorized |
| `decklist enable-background` | Add 1 Background slot to the Commander category |
| `decklist disable-background` | Remove Background slot; all Commander cards move to Uncategorized |
| `decklist enable-companion` | Add a separate Companion slot (1 card, outside the main 100) |
| `decklist disable-companion` | Remove Companion slot; companion card moves to Uncategorized |
| `decklist apply-template <name>` | Replace all user-created categories with the named template's layout; displaced cards move to Uncategorized |

### `category` commands

| Command | Description |
|---|---|
| `category create <name> <slot-count>` | Add a new category with 1–99 slots |
| `category list` | List all categories with filled/total slot counts |
| `category rename <name>` | Interactively rename a category (prompts for new name; user categories only) |

### `card` commands

| Command | Description |
|---|---|
| `card add <category> <card-name>` | Add a card to a category (fills one slot); fails if category is full, card already exists in a capped category, or the `allowed_cards` constraint is violated |
| `card remove <card-name>` | Soft-remove: move card from its current category to the Uncategorized holding area; creates Uncategorized if absent; fails if card is already in Uncategorized |
| `card move <card-name> <category>` | Move a card from its current category to a different one (fails if target is full, does not exist, or the card is not user-addable to that target) |
| `card delete <card-name>` | Hard-delete: permanently remove a card from the decklist; does not place it in Uncategorized |
| `card list [category]` | List all cards, or only cards in the given category |

### `template` commands

| Command | Description |
|---|---|
| `template list` | List all available templates (built-in and user-saved) |
| `template save <name>` | Save the current decklist's user-created categories as a named template |
| `template export <name> <filepath>` | Write a template to a file |
| `template import <filepath>` | Load a template file and save it as a user template |

### REPL built-in commands

| Command | Description |
|---|---|
| `help` | Print available commands |
| `quit` / `exit` | Exit the REPL |

---

## Domain Model (detailed)

### `Category` ABC (`models.py`)

```python
class Category(ABC):
    name: str
    fixed: bool              # True for system-managed categories (Commander, Basic Lands, Companion, Uncategorized)
    allowed_cards: frozenset[str] | None   # None means any card is allowed
    user_addable: bool       # False for Uncategorized (card move cannot target it)
    cards: list[str]         # ordered; duplicates allowed in UncappedCategory

    @property @abstractmethod
    def filled(self) -> int: ...

    @property @abstractmethod
    def is_full(self) -> bool: ...

    @property @abstractmethod
    def available(self) -> int | None: ...  # None for uncapped


@dataclass
class CappedCategory(Category):
    """Fixed upper bound (1–99 slots). Rejects total_slots outside range."""
    total_slots: int          # validated: 1–99


@dataclass
class UncappedCategory(Category):
    """No upper bound. Used for Basic Lands and Uncategorized."""
    # available → None, is_full → False always
```

### `Decklist` (`models.py`)

```python
@dataclass
class Decklist:
    name: str
    categories: dict[str, Category]   # keyed by lowercase name for lookup
    partners_enabled: bool = False
    background_enabled: bool = False
    companion_enabled: bool = False

    # Factory
    @classmethod
    def create(cls, name: str) -> "Decklist": ...
        # Auto-creates: Commander (CappedCategory, 1 slot, fixed=True)
        #               Basic Lands (UncappedCategory, fixed=True, allowed_cards=BASIC_LAND_NAMES)

    # Category operations
    def add_category(self, name: str, slots: int) -> None: ...
    def rename_category(self, old: str, new: str) -> None: ...

    # Card operations
    def add_card(self, card: str, category_name: str) -> None: ...
        # Enforces: category existence, allowed_cards whitelist, fullness,
        # singleton exclusivity across all CappedCategory instances
    def find_card(self, card: str) -> str | None: ...
        # Returns the category key containing this card, or None
    def remove_card(self, card: str) -> None: ...
        # Move card to Uncategorized (creates it if absent). Raises ValueError if not found.
    def delete_card(self, card: str) -> None: ...
        # Permanently remove. Raises ValueError if not found.
    def move_card(self, card: str, to_category_name: str) -> None: ...
        # Validates target (exists, allowed_cards, capacity, exclusivity),
        # then atomically removes from source and appends to target.
        # Does NOT call add_card internally (avoids spurious exclusivity failure).

    # Fixed-slot mode methods
    def enable_partners(self) -> None: ...    # Expands Commander.total_slots by 1
    def disable_partners(self) -> None: ...  # Shrinks Commander by 1, evacuates Commander cards to Uncategorized
    def enable_background(self) -> None: ...  # Expands Commander.total_slots by 1
    def disable_background(self) -> None: ... # Shrinks Commander by 1, evacuates Commander cards to Uncategorized
    def enable_companion(self) -> None: ...   # Creates CappedCategory("Companion", 1, fixed=True)
    def disable_companion(self) -> None: ...  # Removes companion category, moves card to Uncategorized

    # Computed properties
    @property
    def total_slots(self) -> int: ...       # Sum of CappedCategory.total_slots only
    @property
    def total_filled(self) -> int: ...      # Sum of filled across all categories
    @property
    def commander_overcrowded(self) -> bool: ...  # Commander has more cards than enabled modes allow
    @property
    def companion_slot_empty(self) -> bool: ...   # Companion enabled but no card added
    def rename(self, new_name: str) -> None: ...
```

`BASIC_LAND_NAMES` — module-level `frozenset[str]` of all 12 valid basic land names (Plains through Snow-Covered Wastes).

---

## Design Decisions

1. **Custom command parser, not a CLI framework.** The REPL reads raw lines; a simple split-and-dispatch is sufficient for the `object verb args` grammar. `click` is used for output (`click.echo`, `click.style`) and interactive prompts (`click.prompt`), but not for command parsing or routing.
2. **Case-insensitive command matching** for object and verb (`Category Create` works the same as `category create`). Card names preserve their original casing.
3. **Multi-word category names are supported** via greedy arg parsing. `card add` uses a greedy longest-prefix match for the category; `card move` uses a greedy longest-suffix match. No quoting required.
4. **Argument order for `card add`**: `card add <category> <card-name...>` — category first (longest-prefix match), then card name (consumes rest of line).
5. **Argument order for `card move`**: `card move <card-name> <to-category>` — natural English order. The longest-suffix of the arg list that matches a known category key is taken as the target; everything before it is the card name.
6. **`card remove` vs `card delete`**: `card remove` is a soft operation (card goes to Uncategorized, persistent warning fires); `card delete` is a hard operation (card is gone). Users can recover a removed card with `card move`.
7. **Session state**: the REPL holds at most one `Decklist` at a time. `decklist create` replaces any existing decklist. `decklist load` and `decklist import` similarly replace.
8. **Save format**: a custom plain-text format (not JSON). The file starts with a `# <name>` header, followed by one section per category. Fixed system categories use plain headings: `Commander`, `Basic Lands`, `Companion`, `Uncategorized`. User-defined categories use `<name> [<n> slots]`. Card lines are `<qty> <card-name>`. Sections are blank-line separated. This format round-trips through `decklist load`; it is not compatible with external tools.
9. **Export format**: up to three sections — `Commander`, `Companion` (only when a companion card is assigned), and `Maindeck` — compatible with Moxfield, Archidekt, and the `decklist import` command. Category structure is discarded. All non-commander, non-companion cards are merged into `Maindeck`, sorted alphabetically by card name.
10. **Companion does not expand Commander**: Partner and Background both expand `Commander.total_slots`. Companion is a wholly separate `CappedCategory`; it does not affect Commander slot count or the `commander_overcrowded` check.
11. **`cards` is a `list[str]`** (not a `set`): preserves insertion order and allows `UncappedCategory` to hold multiple copies of the same basic land. `CappedCategory` enforces singleton exclusivity at `add_card`/`move_card` time.
12. **I/O is split by purpose**: persistent storage lives in `storage.py` (`PlaintextRepository`, `SqliteRepository`, plus the plain-text format helpers `_format_save_file` / `_parse_save_file` that they share). External interop — `_format_export_file` and `_parse_import_file` (Moxfield/Archidekt) — stays in `commands.py` because it is user-facing format conversion, not deck-library state. `commands.py` re-exports the storage helpers for backward compatibility.
13. **Storage backend is opt-in**: the default is `PlaintextRepository` (single `decklist.bak`); users opt into `SqliteRepository` by setting `{"storage_backend": "sqlite"}` in `config.json`. Multi-deck commands (`decklist list/switch/delete`) work with either backend — Plaintext just sees a one-element library.
