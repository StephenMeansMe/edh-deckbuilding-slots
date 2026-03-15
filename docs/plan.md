# Plan: CLI CRUD Commands (`object verb` style)

> **Status**: Core MVP, card management, file I/O, decklist import, Partner, Background, Companion, Template system, and Scryfall validation are all shipped. This document reflects the current implementation.

## Command Grammar

All commands follow the pattern:

```
<object> <verb> [arguments...]
```

Three objects, each with standard CRUD verbs plus domain-specific operations:

### `decklist` commands

| Command | Description |
|---|---|
| `decklist create <name>` | Create a new decklist; auto-creates `Commander` (1 fixed slot) and `Basic Lands` (uncapped, basic lands only) categories |
| `decklist show` | Print summary: decklist name, each category with filled/total slots, grand total |
| `decklist rename <new-name>` | Rename the current decklist |
| `decklist export <filename>` | Export to Moxfield/Archidekt-compatible plain text file (Commander, optional Companion, Maindeck sections) |
| `decklist save <filename>` | Save decklist structure to a file (categories, slots, cards) |
| `decklist load <filename>` | Load decklist structure from a file |
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

#### Planned (not yet implemented)

| Command | Description |
|---|---|
| `category show <name>` | Show one category's details: slot counts and card names |
| `category resize <name> <slot-count>` | Change a category's total slots (cannot go below current filled count) |
| `category delete <name>` | Delete a category (fails if it contains cards; fixed categories cannot be deleted) |

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

## Domain Model

### `Category` (ABC, in `src/deckslots/models.py`)

`Category` is an abstract base class. Two concrete subclasses are used:

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

### `Decklist` (dataclass, in `src/deckslots/models.py`)

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
    # (resize and delete are handled entirely in command handlers)

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

## File Layout

```
src/deckslots/
├── __init__.py           — package init
├── cli.py                — parse_command(), ParsedCommand dataclass; known objects/builtins
├── models.py             — Category ABC, CappedCategory, UncappedCategory, Decklist, BASIC_LAND_NAMES
├── commands.py           — Session, all handler functions, dispatch registry, save/load/export/import I/O
├── repl.py               — run_repl(); session loop, warning injection, Scryfall loading
├── scryfall.py           — Scryfall API integration: fetch, cache, validate
├── templates.py          — Template model, built-in/user template I/O
├── config.py             — User config (XDG-compliant, validation_enabled flag)
├── exceptions.py         — Custom exception hierarchy (DecklistError and subclasses)
├── logging_config.py     — Debug logging setup (XDG-compliant)
└── data/templates/
    └── goldfish-fundamentals.tmpl   — built-in template

tests/
├── __init__.py
├── test_cli.py                — ParsedCommand parser tests
├── test_models.py             — Category subclasses and Decklist model tests
├── test_commands.py           — handler, save/load/export/import tests
├── test_repl_functional.py    — REPL integration tests
├── test_scryfall.py           — Scryfall integration tests
├── test_templates.py          — Template I/O tests
├── test_exceptions.py         — Exception behavior tests
├── test_logging_config.py     — Logging setup tests
└── functional/                — scrut black-box CLI tests (*.md)
```

Note: `io.py` was not created; all file I/O (`_format_save_file`, `_parse_save_file`, `_format_export_file`, `_parse_import_file`) lives in `commands.py`.

---

## Implementation Phases

### Phase 1 — `Category` model ✓

1. `Category` basics: construct with name, total_slots, empty card list; `filled` returns 0, `available` returns total_slots.
2. `Category` slot constraints: reject total_slots < 1 or > 99 with `ValueError`.
3. `Category.add_card` / `Category.remove_card`: add a card name to the list (fail if full / not present).
4. `Category.fixed` flag: Commander categories are marked `fixed=True`; fixed categories reject deletion.

### Phase 2 — `Decklist` model ✓

5. `Decklist.create`: factory that creates a decklist with mandatory Commander and Basic Lands categories.
6. `Decklist.add_category`: add a user-defined category; reject duplicate names.
7. `Decklist.remove_category`: remove a category; reject if fixed or contains cards.
8. `Decklist.rename_category` and `Decklist.resize_category`: rename rejects duplicates; resize rejects shrinking below filled count.
9. `Decklist.add_card`: add card to a named category; reject if card already exists in any CappedCategory (singleton exclusivity), category is full, or `allowed_cards` violated.
10. `Decklist.total_slots`, `Decklist.total_filled`: aggregate queries.

### Phase 3 — Command parser and dispatcher ✓

11. Command parser: split input into `(object, verb, args)` tuple; return a parse result or error for malformed input.
12. Dispatch table: map `(object, verb)` pairs to handler callables; raise on unknown object/verb.
13. `help` and `quit`/`exit` built-in commands.

### Phase 4 — Command handlers ✓

14. `decklist create`, `decklist show`, `decklist rename` handlers.
15. `category create`, `category list`, `category show` handlers.
16. `category resize`, `category rename`, `category delete` handlers.
17. `card add` handler (with `_resolve_category_and_card` greedy longest-prefix helper).
18. Error feedback: all domain errors caught and printed as user-friendly messages.

### Phase 5 — Card management ✓

19. `Decklist.find_card`, `Decklist.remove_card`, `Decklist.delete_card`, `Decklist.move_card` model methods.
20. `handle_card_delete`, `handle_card_remove`, `handle_card_move` handlers.
21. `_resolve_card_and_category_suffix` — greedy longest-suffix match helper (used by `card move`).

### Phase 6 — File I/O ✓

22. `decklist export`: write Moxfield/Archidekt-compatible plain text.
23. `decklist save`: serialize decklist structure to internal plain-text save format.
24. `decklist load`: deserialize and restore a decklist from a saved file.
25. `Category` model refactored to ABC + `CappedCategory` / `UncappedCategory`; `Basic Lands` auto-created as `UncappedCategory(allowed_cards=BASIC_LAND_NAMES)`.

### Phase 7 — Decklist import ✓

26. `ParsedImport` dataclass: `commander`, `basic_lands`, `uncategorized` fields.
27. `_parse_import_file`: reads `Commander` / `Maindeck` headings, routes cards.
28. `handle_decklist_import`: creates new decklist from parsed import; warns if Uncategorized non-empty.

### Phase 8 — Partner commanders ✓

29. `Decklist.enable_partners` / `disable_partners`: expand/contract Commander slot; evacuate on disable.
30. `commander_overcrowded` property; REPL warning injection.
31. `handle_decklist_enable_partner` / `handle_decklist_disable_partner` handlers.

### Phase 9 — Background commanders ✓

32. `Decklist.enable_background` / `disable_background`: same pattern as Partner (expands Commander slot).
33. `handle_decklist_enable_background` / `handle_decklist_disable_background` handlers.

### Phase 10 — Companion slot ✓

34. `Decklist.enable_companion` / `disable_companion`: creates/removes a separate `CappedCategory("Companion", 1, fixed=True)`.
35. `companion_slot_empty` property; REPL warning injection.
36. `handle_decklist_enable_companion` / `handle_decklist_disable_companion` handlers.
37. Save/load: `Companion` plain heading (like `Commander`) in internal save format.
38. Export: optional `Companion` section between `Commander` and `Maindeck`; companion card excluded from Maindeck.
39. Import (`_parse_import_file`): recognizes `Companion` heading; `ParsedImport.companion` field; `handle_decklist_import` calls `enable_companion()` and adds the card.

---

## Design Decisions

1. **Custom command parser, not a CLI framework**. The REPL reads raw lines; a simple split-and-dispatch is sufficient for the `object verb args` grammar. `click` is used for output (`click.echo`, `click.style`) and interactive prompts (`click.prompt`), but not for command parsing or routing.
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
12. **I/O lives in `commands.py`**: the planned `io.py` module was never created. `_format_save_file`, `_parse_save_file`, `_format_export_file`, and `_parse_import_file` are private functions in `commands.py`.
