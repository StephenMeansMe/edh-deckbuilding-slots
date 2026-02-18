# Plan: CLI CRUD Commands (`object verb` style)

## Command Grammar

All commands follow the pattern:

```
<object> <verb> [arguments...]
```

Three objects, each with standard CRUD verbs plus domain-specific operations:

### `decklist` commands

| Command | Description |
|---|---|
| `decklist create <name>` | Create a new decklist; auto-creates a "Commander" category with 1 fixed slot |
| `decklist show` | Print summary: decklist name, each category with filled/total slots, grand total |
| `decklist rename <new-name>` | Rename the current decklist |
| `decklist export <filename>` | Export to flat text file in `1 Card Name` format |
| `decklist save <filename>` | Save decklist structure to a file (categories, slots, cards) |
| `decklist load <filename>` | Load decklist structure from a file |

### `category` commands

| Command | Description |
|---|---|
| `category create <name> <slot-count>` | Add a new category with 1–99 slots |
| `category list` | List all categories with filled/total slot counts |
| `category show <name>` | Show one category's details: slot counts and card names |
| `category resize <name> <slot-count>` | Change a category's total slots (cannot go below current filled count) |
| `category rename <old-name> <new-name>` | Rename a category |
| `category delete <name>` | Delete a category (fails if it contains cards; Commander category cannot be deleted) |

### `card` commands

| Command | Description |
|---|---|
| `card add <card-name> <category>` | Add a card to a category (fills one slot); fails if category is full or card already exists in decklist |
| `card remove <card-name>` | Remove a card from wherever it is (frees one slot) |
| `card move <card-name> <category>` | Move a card to a different category (fails if target is full) |
| `card list [category]` | List all cards, or only cards in the given category |

### REPL built-in commands

| Command | Description |
|---|---|
| `help` | Print available commands |
| `quit` / `exit` | Exit the REPL |

---

## Domain Model (set-based slots)

Since slots are treated as a set, a category only needs to track its **total capacity** and the **set of card names** it contains. There is no slot identity or card ordering.

### `Category` (dataclass, in `src/deckslots/models.py`)

```python
@dataclass
class Category:
    name: str
    total_slots: int          # 1–99
    cards: set[str]           # card names currently filling slots
    fixed: bool = False       # True for the Commander category

    @property
    def filled(self) -> int: ...

    @property
    def available(self) -> int: ...

    def is_full(self) -> bool: ...
```

### `Decklist` (dataclass, in `src/deckslots/models.py`)

```python
@dataclass
class Decklist:
    name: str
    categories: dict[str, Category]   # keyed by lowercase name for lookup

    # Factory
    @classmethod
    def create(cls, name: str) -> "Decklist": ...
        # auto-creates Commander category (1 fixed slot)

    # Category operations
    def add_category(self, name: str, slots: int) -> Category: ...
    def remove_category(self, name: str) -> None: ...
    def rename_category(self, old: str, new: str) -> None: ...
    def resize_category(self, name: str, slots: int) -> None: ...

    # Card operations
    def add_card(self, card_name: str, category_name: str) -> None: ...
    def remove_card(self, card_name: str) -> None: ...
    def move_card(self, card_name: str, target_category: str) -> None: ...
    def find_card(self, card_name: str) -> Category | None: ...

    # Queries
    @property
    def total_slots(self) -> int: ...
    @property
    def total_filled(self) -> int: ...
    def all_cards(self) -> dict[str, str]: ...  # card_name -> category_name
```

---

## New File Layout

```
src/deckslots/
├── __init__.py          (existing, unchanged)
├── cli.py               (existing, modified — pass args to REPL or dispatch)
├── repl.py              (existing, modified — integrate command dispatcher)
├── models.py            (NEW — Category, Decklist)
├── commands.py          (NEW — command dispatcher + handler functions)
└── io.py                (NEW — save/load/export logic)

tests/
├── __init__.py          (existing, unchanged)
├── test_repl.py         (existing, extended with command integration tests)
├── test_models.py       (NEW — unit tests for Category, Decklist)
├── test_commands.py     (NEW — tests for command parsing and dispatch)
└── test_io.py           (NEW — tests for file I/O)
```

---

## Implementation Phases (TDD order)

Each numbered step is a Red-Green-Refactor cycle and gets its own commit(s).

### Phase 1 — `Category` model

1. **`Category` basics**: construct with name, total_slots, empty card set; `filled` returns 0, `available` returns total_slots.
2. **`Category` slot constraints**: reject total_slots < 1 or > 99 with `ValueError`.
3. **`Category.add_card`** / **`Category.remove_card`**: add a card name to the set (fail if full / not present).
4. **`Category.fixed` flag**: Commander categories are marked `fixed=True`; fixed categories reject deletion later.

### Phase 2 — `Decklist` model

5. **`Decklist.create`**: factory that creates a decklist with a mandatory Commander category (1 fixed slot).
6. **`Decklist.add_category`**: add a user-defined category; reject duplicate names.
7. **`Decklist.remove_category`**: remove a category; reject if fixed or if it contains cards.
8. **`Decklist.rename_category`** and **`Decklist.resize_category`**: rename rejects duplicates; resize rejects shrinking below filled count.
9. **`Decklist.add_card`**: add card to a named category; reject if card already exists anywhere in the decklist (exclusive), or category is full.
10. **`Decklist.remove_card`**: find and remove a card from whatever category it's in.
11. **`Decklist.move_card`**: remove from current category, add to target; reject if target is full.
12. **`Decklist.total_slots`**, **`Decklist.total_filled`**, **`Decklist.all_cards`**: aggregate queries.

### Phase 3 — Command parser and dispatcher

13. **Command parser**: split input into `(object, verb, args)` tuple; return a parse result or error for malformed input.
14. **Dispatch table**: map `(object, verb)` pairs to handler callables; raise on unknown object/verb.
15. **`help` and `quit`/`exit` built-in commands**: these are single-word commands, not `object verb`.

### Phase 4 — Command handlers (wiring domain to REPL)

16. **`decklist create`** handler: creates a `Decklist`, stores it as REPL session state, prints confirmation.
17. **`decklist show`** handler: prints formatted summary of decklist.
18. **`category create`** handler: parses name + slot count, calls `Decklist.add_category`, prints confirmation.
19. **`category list`** and **`category show`** handlers.
20. **`category resize`**, **`category rename`**, **`category delete`** handlers.
21. **`card add`** handler: parses card name + category, calls `Decklist.add_card`.
22. **`card remove`**, **`card move`**, **`card list`** handlers.
23. **`decklist rename`** handler.
24. **Error feedback**: all domain errors (`ValueError`, `KeyError`, etc.) are caught and printed as user-friendly messages, never tracebacks.

### Phase 5 — File I/O

25. **`decklist export`**: write the decklist to a flat text file in `1 Card Name` format, grouped by category.
26. **`decklist save`**: serialize decklist structure (categories, slot counts, card assignments) to a text/JSON file.
27. **`decklist load`**: deserialize and restore a decklist from a saved file.

### Phase 6 — Integration and polish

28. **Wire dispatcher into `repl.py`**: replace the "Unknown command" catch-all with the real dispatcher; keep "Unknown command" as fallback for unrecognized input.
29. **Update existing REPL tests**: ensure the existing 7 tests still pass (some may need adjustment since known commands will no longer be rejected).
30. **End-to-end REPL test**: simulate a full session (create decklist → add categories → add cards → show → export) through mocked input/output.

---

## Design Decisions

1. **No external CLI library** (no `click`, no `argparse` subcommands). The REPL already reads raw lines; a simple split-and-dispatch is sufficient and avoids coupling to a framework.
2. **Case-insensitive command matching** for object and verb (`Category Create` works the same as `category create`). Card names preserve their original casing.
3. **Category names may contain spaces** if we quote them or use a delimiter. For MVP simplicity: **single-word category names only** (e.g., `Ramp`, `Removal`, `Card-Draw`). Spaces in card names are handled by treating everything after the category argument as the card name, or vice versa.
4. **Argument order for `card add`**: `card add <category> <card-name...>` — category first (single token), then card name (may contain spaces, consumes rest of line). This avoids the need for quoting card names.
5. **Session state**: the REPL holds at most one `Decklist` at a time. `decklist create` replaces any existing decklist (with a confirmation prompt if one already exists). `decklist load` similarly replaces.
6. **Save format**: JSON (simple, human-readable, stdlib `json` module). Export format remains `1 Card Name` per the MVP spec.
