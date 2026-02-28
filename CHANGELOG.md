# Changelog

All notable changes to this project will be documented in this file.

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
