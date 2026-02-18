# User Story 002: Import a Decklist from a Text File

## Story

**As an** EDH deckbuilder with existing decklists exported from other tools,
**I want to** import a decklist file in `$QUANTITY $CARDNAME` format,
**so that** I don't have to re-enter my cards manually and can immediately start
organizing them into categories within deckslots.

## Background

Popular deckbuilding tools (Moxfield, Archidekt, Manabox, etc.) can export
decklists as plain text files with `Commander` and `Maindeck` section headings.
The import command reads such a file, routes the commander to its fixed slot and
basic lands to their fixed category, and deposits all remaining cards into a
temporary **Uncategorized** category for the user to sort later.

## Acceptance Criteria

### Parsing and routing

1. `decklist import <filepath>` reads a plain text file and creates a new active
   decklist whose name is derived from the filename (stem, without extension).
2. The file format is:
   ```
   Commander
   1 <card-name>

   Maindeck
   <quantity> <card-name>
   <quantity> <card-name>
   ...
   ```
   - Section headings are the bare words `Commander` and `Maindeck` on their own
     lines (case-insensitive).
   - Each card line is `<integer quantity> <card name>` separated by a single
     space; card names may contain spaces (e.g., `1 Atraxa, Praetors' Voice`).
   - Blank lines and lines that do not match either pattern are silently skipped.
3. The card under the `Commander` heading is placed in the Commander category
   slot (quantity is always treated as 1; any stated quantity is ignored).
4. Cards under the `Maindeck` heading whose names appear in `BASIC_LAND_NAMES`
   are placed in the Basic Lands category, one entry per copy (e.g., `4 Forest`
   → four `"Forest"` entries in `basic lands`).
5. All other `Maindeck` cards are placed in the **Uncategorized** category, one
   entry per copy.
6. The Uncategorized category is a fixed, uncapped category with no
   `allowed_cards` restriction. It is created automatically on import and
   persists as part of the decklist.

### Validation and warnings

7. After a successful import, the app prints a summary:
   ```
   Imported '<name>': 1 commander, <n> basic lands, <m> uncategorized cards.
   ```
8. Whenever the active decklist contains cards in the Uncategorized category,
   every command response is prefixed with a persistent warning:
   ```
   Warning: <n> card(s) in Uncategorized. Assign them to categories before
   finalizing your decklist.
   ```
9. The warning disappears once Uncategorized is empty.
10. `decklist import` returns an error (without modifying session state) if the
    file does not exist or is unreadable.
11. `decklist import` returns an error if the file contains no recognizable card
    lines.

### Edge cases

12. If the Commander section is absent or empty, the Commander slot remains
    empty and the warning message notes the missing commander.
13. If the Maindeck section is absent or empty, only the commander is imported
    (all other acceptance criteria still apply).
14. An existing active decklist is replaced by the import without prompting (the
    old decklist is discarded).

## Notes

- The Uncategorized category is exclusively a holding area produced by import.
  It is never created by `decklist create`. A user cannot add cards to it
  manually via `card add`.
- Moving cards **out** of Uncategorized into proper categories requires a
  `card move` command (out of scope for this story — see future work below).
- Singleton exclusivity (the rule that a card may only appear once across all
  capped categories) does **not** apply to Uncategorized, because Uncategorized
  is uncapped. A card in Uncategorized may later be added to a capped category
  without triggering a duplicate error; the user is responsible for subsequently
  removing it from Uncategorized.
- No semantic validation is performed on import: any string that matches the
  line format is accepted as a card name.

## Future Work (out of scope)

- **`card move <from-category> <to-category> <card-name>`** — atomically moves a
  card between categories; the primary mechanism for emptying Uncategorized.
- **`card remove <category> <card-name>`** — removes a card from a category
  without placing it elsewhere.
- **Conflict detection on import** — warn when a card appears more than once in
  the Maindeck section (would create duplicates in Uncategorized).
- **Alternative section headings** — support `Deck`, `Mainboard`, or headless
  files from tools with different export formats.
