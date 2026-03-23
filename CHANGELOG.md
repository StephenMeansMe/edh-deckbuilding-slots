# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] — 2026-03-22

### Added

- **Companion slot** (#45)
  - `decklist enable-companion` creates a separate, fixed 1-slot Companion zone
    (matching the MTG companion mechanic — distinct from Commander slots).
  - `decklist disable-companion` removes the zone.
  - Save/load and export/import round-trip the Companion section; export emits
    a `Companion` block between Commander and Maindeck when a card is present.
  - The REPL warns after every command when companion mode is on but the slot
    is empty.

- **Template system** (#59)
  - `template list` shows all available templates (built-in and user-saved).
  - `template save <name>` captures the current deck's category structure as a
    reusable template.
  - `template export <name> <file>` and `template import <file>` share
    templates across machines.
  - `decklist create --template <name>` creates a new deck pre-populated with
    a template's category layout. Includes a built-in "Goldfish Fundamentals"
    template with 8 predefined categories.
  - Templates are stored in the XDG user data directory; cards from removed
    categories are evacuated to Uncategorized.

- **Scryfall card validation** (#62)
  - Cards added via `card add` or `card move` are validated against the
    Scryfall database and checked for Commander format legality. Basic lands
    are exempt.
  - Validation data is cached locally (XDG cache dir, 7-day staleness). On
    first use in interactive mode the app prompts to download; non-interactive
    mode silently skips.
  - Set `validation_enabled: false` in `config.json` to opt out globally.

- **Category resize, delete, and filter** (#68)
  - `category resize <name> <slots>` changes the slot cap of any user-created
    category. Fixed categories (Commander, Basic Lands, Uncategorized) are
    protected.
  - `category delete <name>` removes a user-created category and evacuates its
    cards to Uncategorized.
  - `category show <name>` displays the slot summary and full card list for any
    category.

- **Status line** (#71)
  - After every REPL command a compact one-line status is shown:
    `<DeckName> (filled/total)` where total counts only capped slots.
  - Status indicators surface active warnings inline: `Uncategorized: N`,
    `Commander overcrowded`, `Companion: empty`, `Validation: OFF`.
  - Displays `No active decklist` when no deck is loaded.

### Changed

- **Improved CLI output and prompts** (#65)
  - All output now goes through `click.echo()` for consistent stream handling.
  - Confirmation prompts use `click.confirm()`, accepting full words like
    "yes"/"no" in addition to "y"/"n".
  - Warning messages are styled yellow/bold via `click.style()` and are
    collected and printed before command output.

### Fixed

- Companion-slot-empty warning no longer fires immediately after running
  `decklist enable-companion` — it is suppressed for the remainder of the
  command that enables the slot (#58).

### Internal

- Custom exception hierarchy (`DecklistError`, `CardError`, `SlotError`,
  `CategoryError`, `FileError`, `ParseError`) replaces bare exception
  handlers (#58).
- Logging infrastructure added; controlled via `DECKSLOTS_LOG_LEVEL` env var
  (silent by default, writes to stderr and a rotating file) (#58).

## [0.2.1] — 2026-03-08

### Added

- **US-007 — Rename Decklist and Categories**
  - `decklist rename` prompts interactively for a new decklist name.
  - `category rename <name>` prompts interactively for a new category name.
    Only user-created categories can be renamed; fixed categories (Commander,
    Basic Lands, Uncategorized) are protected.

- **US-008 — Partner Commanders**
  - `decklist enable-partners` expands the Commander slot to 2, allowing two
    Partner commanders to be added.
  - `decklist disable-partners` reverses the expansion, evacuating all
    Commander cards to Uncategorized.

- **US-009 — Background Commanders**
  - `decklist enable-background` expands the Commander slot by 1 (to 2 by
    default, to 3 if partners are also enabled), allowing a Background
    co-commander alongside the main commander.
  - `decklist disable-background` reverses the expansion, evacuating all
    Commander cards to Uncategorized.
  - Partners and Background modes are fully composable: enabling both gives
    3 Commander slots.

### Changed

- **Save format simplified** (closes #42): the Commander section heading is
  now always written as plain `Commander` (never `Commander [partners]`).
  On load, Commander's slot count is set dynamically from the number of cards
  present, providing full backwards compatibility with old save files.

- **Persistent overcrowded warning**: after loading a save file whose
  Commander section contains more cards than the current modes allow, a
  warning is displayed after every command until the situation is resolved.

### Refactored

- Category model uses an ABC hierarchy (`Category` abstract base,
  `CappedCategory`, `UncappedCategory` concrete classes) with a shared
  `Protocol` for duck-typed usage, replacing the previous flat dataclass.

## [0.1.0] — 2026-02-28

First public release. Ships the complete MVP: a Linux CLI for organising a
100-card EDH Commander decklist into named category slots.

### Added

- **US-001 — Create decklist with categorised slots**
  - `decklist create <name>` opens a new decklist with mandatory Commander
    (1 fixed slot) and Basic Lands (uncapped, whitelisted) categories.
  - `category create <name> <slots>` adds a user-defined slot category (1–99
    slots).
  - `category list` shows every category with its filled/total counts.
  - `decklist show` prints a full summary of the active decklist.

- **US-002 — Import decklist from file**
  - `decklist import <file>` reads a plain-text file in `$QUANTITY $CARDNAME`
    format with `Commander` and `Maindeck` section headings.
  - The commander is routed to the Commander slot, basic lands to Basic Lands,
    and all other cards to a temporary Uncategorized category.
  - The app warns persistently until Uncategorized is empty.

- **US-003 — Card management**
  - `card add <category> <card-name>` places a card in a named category.
  - `card move <card-name> <to-category>` relocates a card between categories.
  - `card remove <card-name>` soft-removes a card to Uncategorized.
  - `card delete <card-name>` permanently removes a card from the decklist.

- **US-004 — Save, load, and auto-resume**
  - `decklist save` and `decklist load` persist the full decklist structure
    (categories, slot counts, card assignments) to an internal plain-text
    format stored at `$XDG_STATE_HOME/deckslots/decklist.bak`.
  - On startup the app auto-loads the last saved decklist if one exists.

- **US-005 — Export decklist**
  - `decklist export <filepath>` writes a Moxfield/Archidekt-compatible file
    with a `Commander` section and a `Maindeck` section (all non-commander
    cards, quantities aggregated, sorted alphabetically). The export format
    is also compatible with `decklist import`.

- **US-006 — Deck consistency checks**
  - `card move` to a card's current category is now a silent no-op, printing
    `'<card>' is already in '<category>'. Nothing to do.`
  - `card move` enforces the singleton non-basic-land rule: if the card
    already occupies a slot in any other capped category, the move is
    rejected with `Error: '<card>' is already in the deck (in '<category>').`
  - `card add` and `card move` reject basic land cards targeted at any
    category other than Basic Lands:
    `Error: Basic lands can only be added to the 'Basic Lands' category.`
  - Moving a basic land card *to* Basic Lands remains permitted.
