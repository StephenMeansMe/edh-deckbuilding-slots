# User Story 004: Save and Load a Decklist

## Story

**As an** EDH deckbuilder,
**I want to** save my work-in-progress and have it automatically load the next
time I start the app,
**so that** I can pick up right where I left off without re-importing or
re-categorising anything.

## Background

Session persistence is a two-part problem:

- **Save** — write the full decklist structure (categories, slot counts, and
  card assignments) to a well-known location the app can later reconstruct
  exactly.
- **Auto-resume** — on the next startup, the app automatically loads that file
  so the user sees their deck immediately.

The app stores the save file at a single fixed path:
`$XDG_STATE_HOME/deckslots/decklist.bak` (defaulting to
`~/.local/state/deckslots/decklist.bak` when `$XDG_STATE_HOME` is unset).
There is only ever one save slot in the MVP.

The save format is an **internal** format: it preserves categories and slot
counts and is not designed for external tools. Sharing a finished deck with
Moxfield, Archidekt, or similar platforms is covered by User Story 005.

## Acceptance Criteria

### `decklist save`

1. Writes the current active decklist to the fixed save path
   (`$XDG_STATE_HOME/deckslots/decklist.bak`) in the deckslots save format
   (defined below). The parent directory is created automatically if it does
   not exist.
2. Returns an error if no decklist is active.
3. Returns an error if the save path cannot be written (bad permissions, etc.).
4. On success, prints:
   ```
   Saved '<name>'.
   ```
5. The Commander category is always written first.
6. User-defined capped categories follow in creation order, each as a named
   section with its slot count in brackets.
7. The Basic Lands category is written after user-defined categories.
8. The Uncategorized category (if present) is written last.
9. Empty categories (no cards yet assigned) are still written so the slot
   structure is preserved on re-load.
10. Cards within each section are written in `<quantity> <card-name>` format,
    with identical card names aggregated (e.g., four copies of `Forest` appear
    as a single `4 Forest` line, not four `1 Forest` lines).
11. Any existing save file is silently overwritten.

#### Save file format

```
# Atraxa Stax

Commander
1 Atraxa, Praetors' Voice

Ramp [8 slots]
1 Sol Ring
1 Cultivate

Removal [6 slots]

Basic Lands
4 Forest
3 Mountain

Uncategorized
1 Doubling Season
```

- The first line is `# <decklist name>`, used to restore the decklist name on
  load.
- The Commander section heading is the bare word `Commander`.
- User-defined capped category headings are `<category-name> [<n> slots]`,
  where `<n>` is `total_slots`.
- The Basic Lands heading is `Basic Lands` (bare, no slot count — it is always
  uncapped).
- The Uncategorized heading is `Uncategorized` (bare, no slot count — it is
  always uncapped).
- Card lines are `<integer quantity> <card name>`.
- Sections are separated by a single blank line.
- No other metadata lines are written.

### `decklist load`

12. Reads the fixed save path (`$XDG_STATE_HOME/deckslots/decklist.bak`) and
    sets the restored decklist as the active decklist, replacing any currently
    active decklist without prompting.
13. Returns an error if the save file does not exist.
14. Returns an error if the file cannot be parsed as a valid save file.
15. On success, prints:
    ```
    Loaded '<name>'.
    ```
    where `<name>` is taken from the `# <name>` line in the file.
16. Restores the full category structure from the save format:
    - `# <name>` (first line) → the decklist name.
    - `Commander` (bare heading) → the Commander category.
    - `<name> [<n> slots]` → a user-defined capped category named `<name>`
      with `total_slots = n`, created before cards are added.
    - `Basic Lands` (bare heading) → the Basic Lands category.
    - `Uncategorized` (bare heading) → the Uncategorized category (fixed,
      uncapped, not user-addable), created on demand.
    - Card lines `<qty> <card>`: `<qty>` copies of `<card>` are added to the
      most recently seen category. Lines that do not match the card-line
      pattern (including blank lines) are silently skipped.
17. The `allowed_cards` whitelist for Basic Lands is enforced during load; an
    error is returned if a non-basic-land card name is found under the
    `Basic Lands` heading.

### Auto-load on startup

18. When the REPL starts, if the save file exists, the app loads it using the
    same logic as `decklist load`.
19. On successful auto-load, prints before the first prompt:
    ```
    Resumed '<name>'.
    ```
20. If the save file does not exist, the REPL starts silently with no active
    decklist (no message).

### General

21. If the active decklist contains cards in Uncategorized, the persistent
    Uncategorized warning (shown before every command response when
    Uncategorized is non-empty) is displayed as usual — the save operation
    still completes successfully.
22. Unsaved in-session changes (e.g., cards added after the last
    `decklist save`) are not persisted automatically. On the next startup the
    app resumes from the last explicitly saved state.

## Notes

- `decklist import` continues to handle the original `Commander` / `Maindeck`
  plain text format (User Story 002) and routes all non-commander,
  non-basic-land cards to Uncategorized; it does not recognise the
  `[<n> slots]` heading syntax or the `# <name>` line.
- An incomplete deck (fewer than 100 cards, or cards in Uncategorized) can be
  saved and re-loaded without error. The persistent Uncategorized warning
  already signals work-in-progress state.
- `$XDG_STATE_HOME` is appropriate for this data: it persists between
  restarts but is not portable enough to live in `$XDG_DATA_HOME`. It defaults
  to `~/.local/state` per the XDG Base Directory Specification.

## Future Work (out of scope)

- **Multiple save slots** — `decklist save <name>` and `decklist load <name>`
  to maintain more than one saved deck.
- **Auto-save** — persist state automatically after every command so the user
  never loses an unsaved change.
- **Overwrite confirmation** — prompt before overwriting the existing save
  file.
- **Database-backed persistence** — replace the flat file with a local
  database for richer querying and history (see Roadmap).
