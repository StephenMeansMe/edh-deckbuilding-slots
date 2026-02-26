# User Story 004: Save and Load a Decklist

## Story

**As an** EDH deckbuilder,
**I want to** save my work-in-progress decklist to a file and have it
automatically load the next time I start the app,
**so that** I can pick up right where I left off without re-importing or
re-categorising anything.

## Background

Session persistence is a two-part problem:

- **Save** — write the full decklist structure (categories, slot counts, and
  card assignments) to a file the app can later reconstruct exactly.
- **Load / auto-resume** — on the next startup, the app automatically opens
  the most recently saved file so the user sees their deck immediately.

The save format is an **internal** format: it preserves categories and slot
counts and is not designed for external tools. Sharing a finished deck with
Moxfield, Archidekt, or similar platforms is covered by User Story 005.

## Acceptance Criteria

### `decklist save <filepath>`

1. Writes the current active decklist to `<filepath>` in the deckslots save
   format (defined below).
2. Returns an error if no decklist is active.
3. Returns an error if `<filepath>` cannot be written (bad path, permissions,
   etc.).
4. On success, records `<filepath>` in the session file
   (`~/.config/deckslots/session`) and prints:
   ```
   Saved '<name>' to '<filepath>'.
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
11. If the destination file already exists it is silently overwritten; no
    confirmation prompt is shown in the MVP.
12. The file extension is not enforced; the user may supply any path (e.g.,
    `my_deck.txt`, `my_deck`).

#### Save file format

```
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

### `decklist load <filepath>`

13. Reads a file written by `decklist save` and sets the restored decklist as
    the active decklist, replacing any currently active decklist without
    prompting.
14. Returns an error if `<filepath>` does not exist or cannot be read.
15. Returns an error if the file cannot be parsed as a valid save file.
16. On success, records `<filepath>` in the session file
    (`~/.config/deckslots/session`) and prints:
    ```
    Loaded '<name>' from '<filepath>'.
    ```
    where `<name>` is the file's stem (filename without extension), matching
    how `decklist import` derives the decklist name.
17. Restores the full category structure from the save format:
    - `Commander` (bare heading) → the Commander category.
    - `<name> [<n> slots]` → a user-defined capped category named `<name>`
      with `total_slots = n`, created before cards are added.
    - `Basic Lands` (bare heading) → the Basic Lands category.
    - `Uncategorized` (bare heading) → the Uncategorized category (fixed,
      uncapped, not user-addable), created on demand.
    - Card lines `<qty> <name>`: `<qty>` copies of `<name>` are added to the
      most recently seen category. Lines that do not match the card-line
      pattern (including blank lines) are silently skipped.
18. The `allowed_cards` whitelist for Basic Lands is enforced during load; an
    error is returned if a non-basic-land card name is found under the
    `Basic Lands` heading.

### Auto-load on startup

19. When the REPL starts, if the session file (`~/.config/deckslots/session`)
    exists and contains a path, the app attempts to load the decklist at that
    path using the same logic as `decklist load`.
20. On successful auto-load, prints before the first prompt:
    ```
    Resumed '<name>' from '<filepath>'.
    ```
21. If the session file exists but the recorded file is missing or unreadable,
    prints a warning and starts with no active decklist:
    ```
    Warning: could not resume session from '<filepath>' — file not found.
    Use 'decklist create', 'decklist import', or 'decklist load' to begin.
    ```
22. If the session file does not exist, the REPL starts silently with no active
    decklist (no message).
23. The session file is stored at `~/.config/deckslots/session`. The parent
    directory is created automatically if it does not exist.

### General

24. `decklist save` and `decklist load` require an active decklist and an
    existing file respectively; see individual criteria above for error cases.
25. If the active decklist contains cards in Uncategorized, the persistent
    Uncategorized warning (shown before every command response when
    Uncategorized is non-empty) is displayed as usual during a session — the
    save operation still completes successfully.
26. Unsaved in-session changes (e.g., cards added after the last `decklist
    save`) are not persisted automatically. On the next startup the app
    resumes from the last explicitly saved state.

## Notes

- The session file (`~/.config/deckslots/session`) contains only the absolute
  path of the most recently saved or explicitly loaded decklist, one line, no
  trailing newline. It is updated by `decklist save` and `decklist load` only
  — `decklist create` and `decklist import` do not touch it.
- `decklist load` is the correct command for explicitly switching to a
  different save file mid-session. `decklist import` continues to handle the
  original `Commander` / `Maindeck` plain text format (User Story 002) and
  routes all non-commander, non-basic-land cards to Uncategorized; it does not
  recognise the `[<n> slots]` heading syntax.
- An incomplete deck (fewer than 100 cards, or cards in Uncategorized) can be
  saved and re-loaded without error. The persistent Uncategorized warning
  already signals work-in-progress state.

## Future Work (out of scope)

- **Auto-save** — write to the session file automatically after every
  command so the user never loses an unsaved change.
- **Named sessions** — maintain a history of save files rather than a single
  last-session pointer, allowing the user to switch between multiple decks by
  name.
- **`decklist save` with name override** — `decklist save <filepath> as
  <name>` sets an explicit decklist name that differs from the filename stem.
- **Overwrite confirmation** — prompt before overwriting an existing file.
- **Database-backed persistence** — replace flat text files with a local
  database for richer querying and history (see Roadmap).
