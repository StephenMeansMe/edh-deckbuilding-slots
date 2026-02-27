# Architecture

The app uses an **object-verb command pattern** with a dispatch registry.

## cli.py

- `parse_command(line)` returns a `ParsedCommand`
- `ParsedCommand` fields: `kind` (`builtin`, `object_verb`, `unknown`, `empty`), `obj`, `verb`, `args`
- Known objects: `decklist`, `category`, `card`
- Builtins: `quit`, `exit`, `help`

## models.py

- Domain models: `Category` and `Decklist`
- `Category` fields: `name`, `total_slots`, `fixed`, `capped`, `allowed_cards`, `cards`
- `Decklist` fields: `name`, `categories` dict
- `Decklist.create()` auto-adds mandatory Commander and Basic Lands categories
- `BASIC_LAND_NAMES` — module-level `frozenset[str]` of all 12 valid basic land names
- `Category.cards` is `list[str]` (allows duplicates for basic lands)
- `Decklist.add_card(card, category_name)` enforces: category existence, `allowed_cards` whitelist, fullness, singleton exclusivity across capped categories (uncapped categories skip the exclusivity check)
- Capped categories validate `1 <= total_slots <= 99`; uncapped validate `total_slots >= 0` with no upper limit
- Uncapped categories return `None` for `available` and `False` for `is_full`

## commands.py

- `Session` holds REPL state (`decklist: Decklist | None`)
- Handler functions (e.g., `handle_decklist_create`) return strings
- `_resolve_category_and_card(args, categories)` — greedy longest-prefix match for `<category> <card>` args (used by `card add`)
- `_resolve_card_and_category_suffix(args, categories)` — greedy longest-suffix match for `<card> <category>` args (used by `card move`)
- Card move/remove operations manipulate `category.cards` directly in handlers — the exclusivity check in `Decklist.add_card()` is **not** re-run during a move
- `register_all_handlers(session)` — builds `dict[tuple[str, str], Callable]` dispatch registry
- `dispatch(cmd, registry)` — routes commands to the appropriate handler

## repl.py

- `run_repl()` — creates a `Session` and registry, then loops on `input()`
- Delegates object-verb commands to `dispatch`
- Delegates the `help` builtin to `handle_help`
