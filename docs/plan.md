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
| `card remove <card-name>` | Soft-remove: move card from its current category to the Uncategorized holding area; creates Uncategorized if absent; fails if card is already in Uncategorized |
| `card move <card-name> <category>` | Move a card from its current category to a different one (fails if target is full, does not exist, or equals Uncategorized) |
| `card delete <card-name>` | Hard-delete: permanently remove a card from the decklist; does not place it in Uncategorized |
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
    def find_card(self, card_name: str) -> Category | None: ...
        # Returns the first Category that contains card_name, or None.
    def remove_card(self, card_name: str) -> str: ...
        # Find and remove card from its category; return the source category
        # name. Raises ValueError if not found. Removes only one occurrence
        # (relevant for uncapped categories with duplicate card names).
    def move_card(self, card_name: str, target_category: str) -> None: ...
        # Validate target (exists, allowed_cards, capacity), then atomically
        # remove from source and append to target. Does not call add_card
        # internally so the singleton-exclusivity check is not re-applied
        # against the source category.

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
    *Not implemented as a model method — card removal is handled directly in `handle_card_remove` and `handle_card_delete` (see Phase 5).*
11. **`Decklist.move_card`**: remove from current category, add to target; reject if target is full.
    *Not implemented as a model method — move/validate logic lives entirely in `handle_card_move` (see Phase 5).*
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

### Phase 5 — Card management (User Story 003)

#### Model additions (`src/deckslots/models.py`)

25. **`Decklist.find_card`**: iterate `self.categories.values()`; return the
    first `Category` whose `cards` list contains the card name, or `None`.
    Tests: found in capped category, found in uncapped category, not found
    returns `None`.

26. **`Decklist.remove_card`**: call `find_card`; raise `ValueError` if
    `None`; call `cat.cards.remove(card)` (removes first occurrence); return
    `cat.name`.
    Tests: removes from capped category, removes only one copy from uncapped,
    raises on missing card.
    *Not implemented as a model method — removal is performed directly in
    `handle_card_remove` and `handle_card_delete` via `cat.cards.remove(card)`,
    keeping all validation in the handlers.*

27. **`Decklist.move_card`**: validate target exists, `allowed_cards`,
    capacity; raise `ValueError` for each failure before mutating; then call
    `source.cards.remove(card)` and `target.cards.append(card)`.
    Do **not** call `add_card` internally (avoids spurious exclusivity failure
    while card is still in source).
    Tests: moves capped→capped, moves uncapped→capped (from Uncategorized),
    raises if target full, raises if target not found, raises if same category,
    raises if `allowed_cards` violated.
    *Not implemented as a model method — all move logic (validation and
    mutation) lives in `handle_card_move` in `commands.py`.*

#### Command handlers (`src/deckslots/commands.py`)

28. **`handle_card_delete`**: require active decklist; join all `cmd.args` as
    the card name; call `session.decklist.remove_card(card)`; return
    `"Deleted '<card>' from the decklist."` on success or a user-friendly error
    string on `ValueError`.
    Tests: deletes from capped category, deletes from Uncategorized, error when
    not found, error when no decklist, error when no args.

29. **`handle_card_remove`**: require active decklist; join all `cmd.args` as
    the card name; call `session.decklist.find_card(card)` first — if the card
    is in Uncategorized, return an error directing the user to `card delete`;
    call `session.decklist.remove_card(card)` to remove from its current
    category; create the Uncategorized `Category` if `"uncategorized"` is not
    already in `session.decklist.categories`; call
    `session.decklist.add_card(card, "Uncategorized")`; return
    `"Removed '<card>' from '<from-cat>'. Card is now in Uncategorized."`.
    Tests: moves card to Uncategorized, creates Uncategorized if absent,
    reuses existing Uncategorized, error if already in Uncategorized, error if
    card not found, error if no decklist.

30. **`_resolve_card_and_category_suffix`** (implemented as this name, not `_resolve_card_and_category`): new helper — greedy longest-suffix match
    for category. Iterate `i` from 1 to `len(args)-1`; join `args[i:]` and
    check against `categories`; return `(" ".join(args[:i]), matched_key)` on
    first (longest-suffix) match, or `None` if no match.
    Tests: single-word category, multi-word category, no match returns `None`,
    prefers longer category match over shorter.

31. **`handle_card_move`**: require active decklist and at least 2 args; call
    `_resolve_card_and_category`; return usage error if unresolved; check that
    `target_cat.user_addable` is `True`, else return an error; call
    `session.decklist.move_card(card, target_cat.name)`; return
    `"Moved '<card>' from '<from-cat>' to '<to-cat>'."`.
    Tests: basic move, move from Uncategorized to capped category, error if
    card not found, error if target not found, error if target full, error if
    targeting Uncategorized, error if already in target category, error if no
    decklist.

#### Registration and help

32. **Register new handlers**: add `("card", "move")`, `("card", "remove")`,
    and `("card", "delete")` to `register_all_handlers`.

33. **Update `handle_help`**: add `card move`, `card remove`, and `card delete`
    entries.

### Phase 6 — File I/O

34. **`decklist export`**: write the decklist to a Moxfield/Archidekt-compatible plain text file with exactly two sections: `Commander` (the commander card, if any) and `Maindeck` (all cards from every other category, quantities aggregated, sorted alphabetically by card name). Category names and slot counts are not written.
35. **`decklist save`**: serialize decklist structure (categories, slot counts, card assignments) to the internal plain-text save format (see Design Decision 8).
36. **`decklist load`**: deserialize and restore a decklist from a saved file.

### Phase 7 — Integration and polish

37. **Wire dispatcher into `repl.py`**: replace the "Unknown command" catch-all with the real dispatcher; keep "Unknown command" as fallback for unrecognized input.
38. **Update existing REPL tests**: ensure the existing 7 tests still pass (some may need adjustment since known commands will no longer be rejected).
39. **End-to-end REPL test**: simulate a full session (create decklist → add categories → add cards → move → remove → delete → show) through mocked input/output.

---

## Design Decisions

1. **No external CLI library** (no `click`, no `argparse` subcommands). The REPL already reads raw lines; a simple split-and-dispatch is sufficient and avoids coupling to a framework.
2. **Case-insensitive command matching** for object and verb (`Category Create` works the same as `category create`). Card names preserve their original casing.
3. **Category names may contain spaces** if we quote them or use a delimiter. For MVP simplicity: **single-word category names only** (e.g., `Ramp`, `Removal`, `Card-Draw`). Spaces in card names are handled by treating everything after the category argument as the card name, or vice versa.
4. **Argument order for `card add`**: `card add <category> <card-name...>` — category first (single token), then card name (may contain spaces, consumes rest of line). This avoids the need for quoting card names.
5. **Argument order for `card move`**: `card move <card-name> <to-category>` — natural English order (move THING to PLACE). Because both card name and category can contain spaces, argument parsing uses `_resolve_card_and_category_suffix`, a greedy longest-suffix match helper that is the mirror of `_resolve_category_and_card`. The longest suffix of the arg list that matches a known category key is taken as the target; everything before it is the card name.
6. **`card remove` vs `card delete`**: `card remove` is a soft operation (card goes to Uncategorized, persistent warning fires); `card delete` is a hard operation (card is gone). This distinction gives users a safety net: accidental removes are visible in Uncategorized and can be recovered with `card move`; intentional deletes are final.
7. **Session state**: the REPL holds at most one `Decklist` at a time. `decklist create` replaces any existing decklist (with a confirmation prompt if one already exists). `decklist load` similarly replaces.
8. **Save format**: a custom plain-text format (not JSON). The file starts with a `# <name>` header, followed by one section per category: `Commander`, `Basic Lands`, user-defined categories as `<name> [<n> slots]`, and `Uncategorized`. Card lines are `<qty> <card-name>`. Sections are blank-line separated. This format is internal and round-trips through `decklist load`; it is not compatible with external tools.
9. **Export format**: two-section plain text — `Commander` and `Maindeck` — compatible with Moxfield, Archidekt, and the `decklist import` command (User Story 005). Category structure is discarded. All non-commander cards are merged into `Maindeck`, sorted alphabetically by card name.
