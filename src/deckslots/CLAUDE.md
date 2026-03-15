# Architecture

The app uses an **object-verb command pattern** with a dispatch registry.

## cli.py

- `parse_command(line)` returns a `ParsedCommand`
- `ParsedCommand` fields: `kind` (`builtin`, `object_verb`, `unknown`, `empty`), `obj`, `verb`, `args`, `raw`, `builtin`
- Known objects: `decklist`, `category`, `card`, `template`
- Builtins: `quit`, `exit`, `help`

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

## commands.py

- `Session` holds REPL state: `decklist: Decklist | None`, `scryfall_index: dict | None`
- Handler functions (e.g., `handle_decklist_create`) return strings
- File I/O helpers (all private, in commands.py — no separate io.py):
  - `_format_save_file(decklist)` / `_parse_save_file(path)` — custom plain-text round-trip format
  - `_format_export_file(decklist)` / `_parse_import_file(path)` — Moxfield/Archidekt-compatible format
- `_resolve_category_and_card(args, categories)` — greedy longest-prefix match for `<category> <card>` args (used by `card add`)
- `_resolve_card_and_category_suffix(args, categories)` — greedy longest-suffix match for `<card> <category>` args (used by `card move`)
- `register_all_handlers(session)` — builds `dict[tuple[str, str], Callable]` dispatch registry covering decklist, category, card, and template handlers
- `dispatch(cmd, registry)` — routes commands to the appropriate handler

## repl.py

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
