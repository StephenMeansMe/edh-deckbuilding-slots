# Roadmap

This document outlines what the **edh-deckbuilding-slots** project delivers today (MVP) and where it is headed in future releases.

---

## MVP — Minimum Viable Product

The MVP is a deliberately narrow slice: a working CLI tool that lets a user organize a 100-card Commander decklist into named categories using the "slots" model.

### Core features

- **Commander slot** — Every decklist has exactly one mandatory fixed slot in its own category for the commander.
- **Partner commanders** — `decklist enable-partner` expands the Commander slot to two cards for the partner mechanic. `decklist disable-partner` reverts to a single commander. *(#53)*
- **Background** — `decklist enable-background` adds a fixed Background slot (one card) alongside the commander for the "choose a Background" mechanic. `decklist disable-background` removes it and moves the card to Uncategorized. *(#54)*
- **Companion** — `decklist enable-companion` adds a separate fixed Companion slot (one card) representing the companion zone outside the main 100. `decklist disable-companion` removes it and moves the card to Uncategorized. *(#55)*
- **User-defined categories** — Users create named categories (e.g., "Ramp," "Removal," "Draw") with 1--99 slots each. Renaming is supported; the following operations are planned but not yet implemented:

  | Command | Description |
  |---|---|
  | `category show <name>` | Show one category's details: slot counts and card names |
  | `category resize <name> <slot-count>` | Change a category's total slots (cannot go below current filled count) |
  | `category delete <name>` | Delete a category (fails if it contains cards; fixed categories cannot be deleted) |
- **Exclusive slot assignment** — Each card occupies exactly one slot in one category. The total slot count across all categories equals 100.
- **Template system** — `template list/save/export/import` manages reusable category configurations. The built-in `goldfish-fundamentals` template provides a standard starting layout. Users can save their own templates and apply them to a decklist with `decklist apply-template <name>`; cards displaced by the new layout move to Uncategorized.

### Interface and I/O

- **Linux CLI** — The only supported interface is a command-line application running on Linux.
- **Decklist import** — `decklist import <file>` reads a plain text file in `$QUANTITY $CARDNAME` format with `Commander` and `Maindeck` section headings. The commander is routed to the Commander slot, basic lands to the Basic Lands category, and all other cards to a temporary **Uncategorized** category. The app persistently warns until Uncategorized is empty. *(#47)*
- **Plain text export** — `decklist export <filepath>` writes a Moxfield/Archidekt-compatible file with up to three sections: `Commander` (the assigned commander(s), if any), `Companion` (the companion card, if any — only present when a companion is assigned), and `Maindeck` (all other cards, quantities aggregated, sorted alphabetically by card name). Category structure is intentionally discarded; external tools apply their own grouping and display logic. The export format is also compatible with `decklist import` *(#50)*.

### Optional semantic validation

- **Scryfall card validation** — The app can optionally warn (not error) when a card name is not found in the Scryfall database, or when a card is found but is not legal in Commander. Validation is opt-in via `config.json`; core decklist operations remain fully offline-capable. Card type and placement (e.g., "sorcery in a Lands category") are still not checked — any valid card name can go in any slot.

---

## Future Releases

Features below are organized by theme. No specific release schedule is attached; they will be prioritized as the project matures.

### Non-exclusive categories

- Allow a card to appear in **multiple** category slots simultaneously (e.g., a card that is both "Ramp" and "Draw").
- Each card must still have one **primary** category slot; additional appearances are marked as secondary.
- The app visually distinguishes primary vs. secondary placements.
- Total slot count may exceed 100 when non-exclusive mode is active.

### Export formats

- **CSV export** — Export decklists as CSV files.

### Scryfall integration (extended)

- Pull richer card data (art, oracle text, pricing, etc.) from the [Scryfall API](https://scryfall.com/docs/api) beyond the current name/legality validation.

### Storage

- **Database-backed persistence** — Replace or supplement flat text files with a local database for richer querying and history.

### Platform and interface

- **GUI** — A graphical interface (toolkit TBD).
- **Non-Linux targets** — macOS and Windows support.
