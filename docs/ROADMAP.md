# Roadmap

This document outlines what the **edh-deckbuilding-slots** project delivers today and where it is headed in future releases.

---

## Current Version

A working CLI tool that lets a user organize a 100-card Commander decklist into named categories using the "slots" model. The features below represent everything shipped to date.

### Core features

- **Commander slot** — Every decklist has exactly one mandatory fixed slot in its own category for the commander.
- **Partner commanders** — `decklist enable-partners` expands the Commander category to 2 slots, supporting the partner mechanic. Partners mode is persisted across save/load. *(User Story 008)*
- **User-defined categories** — Users create named categories (e.g., "Ramp," "Removal," "Draw") with 1--99 slots each.
- **Exclusive slot assignment** — Each card occupies exactly one slot in one category. The total slot count across all categories equals 100.
- **Pre-configured starter categories** — The app ships with optional category suggestions (Lands, Ramp, Removal, Draw, Enablers, Payoffs) that the user can adopt, modify, or ignore.
- **Card management** — `card add`, `card move`, `card remove`, and `card delete` let users add cards to categories, move them between categories, remove them from a category (returning them to Uncategorized), and delete them from the decklist entirely. *(User Story 003)*
- **Rename** — `decklist rename` and `category rename` let users rename the active decklist or any user-defined category. *(User Story 007)*
- **Consistency checks** — `decklist check` reports whether the decklist is valid: exactly 100 cards, no Uncategorized cards, Commander slot filled. *(User Story 006)*

### Interface and I/O

- **Linux CLI** — The only supported interface is a command-line application running on Linux.
- **Save and load** — `decklist save` persists the active decklist to disk; the app auto-resumes the last saved decklist on startup. *(User Story 004)*
- **Decklist import** — `decklist import <file>` reads a plain text file in `$QUANTITY $CARDNAME` format with `Commander` and `Maindeck` section headings. The commander is routed to the Commander slot, basic lands to the Basic Lands category, and all other cards to a temporary **Uncategorized** category. The app persistently warns until Uncategorized is empty. *(User Story 002)*
- **Plain text export** — `decklist export <filepath>` writes a Moxfield/Archidekt-compatible file with two sections: `Commander` (the assigned commander, if any) and `Maindeck` (all other cards, quantities aggregated, sorted alphabetically by card name). Category structure is intentionally discarded; external tools apply their own grouping and display logic. The export format is also compatible with `decklist import`. *(User Story 005)*

### Intentional omissions

- **No semantic validation** — The app does not check whether a card is legal, whether a sorcery was placed in a "Lands" category, or whether the commander is actually a legendary creature. Any string can go in any slot.

---

## Future Releases

Features below are organized by theme. No specific release schedule is attached; they will be prioritized as the project matures.

### Additional fixed slots

- **Background** — A fixed slot for the Background enchantment (paired with a "choose a Background" commander).
- **Companion** — A fixed slot for a companion creature that lives outside the main 100.

### Non-exclusive categories

- Allow a card to appear in **multiple** category slots simultaneously (e.g., a card that is both "Ramp" and "Draw").
- Each card must still have one **primary** category slot; additional appearances are marked as secondary.
- The app visually distinguishes primary vs. secondary placements.
- Total slot count may exceed 100 when non-exclusive mode is active.

### Export formats

- **CSV export** — Export decklists as CSV files.
- ~~**Third-party tool compatibility** — Export in formats recognized by Archidekt, Moxfield, and other popular deckbuilding platforms.~~ *(Covered by plain text export, which is already Moxfield/Archidekt-compatible.)*

### Scryfall integration

- Pull card data (art, oracle text, legality, pricing, etc.) from the [Scryfall API](https://scryfall.com/docs/api) as an optional enrichment layer.
- Core decklist operations remain fully **offline-capable** — Scryfall data is never required to add or remove cards.
- When enabled, the app **warns** (does not error) if:
  - A card name is not found in the Scryfall database.
  - A card is found but is not legal in the Commander format.

### Storage

- **Database-backed persistence** — Replace or supplement flat text files with a local database for richer querying and history.

### Platform and interface

- **GUI** — A graphical interface (toolkit TBD).
- **Non-Linux targets** — macOS and Windows support.
