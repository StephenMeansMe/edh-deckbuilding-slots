# User Story 004: Save and Export a Decklist

## Story

**As an** EDH deckbuilder,
**I want to** save my decklist to a file and re-load it in a later session,
and separately export it as a plain text file with only `Commander` and
`Maindeck` headings,
**so that** I can pick up where I left off without starting over, and share my
finished deck with online tools such as Moxfield or Archidekt.

## Background

Two distinct file operations serve different needs:

- **Save** — produces an internal format that preserves the full decklist
  structure (categories, slot counts, and card assignments). A saved file can
  be re-loaded by an extended `decklist import` command in a future session
  (see Future Work below).
- **Export** — produces a simplified format (`Commander` and `Maindeck`
  sections only, quantities aggregated) that is compatible with popular
  deckbuilding platforms. Category information is intentionally discarded.

## Acceptance Criteria

### `decklist save <filepath>`

1. Writes the current active decklist to `<filepath>` in the deckslots save
   format (defined below).
2. Returns an error if no decklist is active.
3. Returns an error if `<filepath>` cannot be written (bad path, permissions,
   etc.).
4. On success, prints:
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

### `decklist export <filepath>`

11. Writes the current active decklist to `<filepath>` in a
    Moxfield/Archidekt-compatible plain text format.
12. Returns an error if no decklist is active.
13. Returns an error if `<filepath>` cannot be written.
14. On success, prints:
    ```
    Exported '<name>' to '<filepath>'.
    ```
15. The export file has exactly two sections: `Commander` and `Maindeck`,
    separated by a blank line.
16. The `Commander` section contains the commander card as `1 <card-name>`. If
    no commander has been assigned, the `Commander` section is written with no
    card lines.
17. The `Maindeck` section contains every card from every non-Commander
    category (including Basic Lands and Uncategorized), with identical card
    names aggregated across all categories.
18. Cards in the `Maindeck` section are sorted alphabetically by card name.
19. Category information is not written to the export file.

#### Export file format

```
Commander
1 Atraxa, Praetors' Voice

Maindeck
1 Cultivate
1 Doubling Season
4 Forest
3 Mountain
1 Sol Ring
```

### General

20. Both commands require an active decklist; return an error if none exists.
21. If the active decklist contains cards in Uncategorized, the persistent
    Uncategorized warning (shown before every command response when
    Uncategorized is non-empty) is displayed as usual — the save and export
    operations still complete successfully.
22. If the destination file already exists it is silently overwritten; no
    confirmation prompt is shown in the MVP.
23. The file extension is not enforced; the user may supply any path (e.g.,
    `my_deck.txt`, `my_deck`).

## Notes

- `decklist save` is the primary mechanism for session persistence in the MVP.
  Database-backed persistence is a future roadmap item.
- Re-loading a saved file in the current MVP is done via `decklist import`.
  Because `import` routes unrecognised section headings' cards to Uncategorized
  and ignores the `[<n> slots]` metadata, the user would lose category
  assignments on re-load. A future extension (see below) will teach `import`
  to recognise the save format and restore full category structure.
- The `export` format is intentionally lossy: category names and slot counts
  are discarded. It is designed for compatibility with external tools, not for
  session resumption.
- An incomplete deck (fewer than 100 assigned cards, or cards remaining in
  Uncategorized) can still be saved and exported without error. The persistent
  Uncategorized warning already signals work-in-progress state.

## Future Work (out of scope)

- **Extend `decklist import` to handle save format** — recognise the
  `[<n> slots]` heading syntax and restore the full category structure (names,
  slot counts) from a save file, rather than routing everything to
  Uncategorized.
- **Export sorting options** — sort Maindeck cards by mana value, by type, or
  by the category they came from.
- **Export format variants** — CSV, JSON, or platform-specific formats
  (Archidekt, Manabox, etc.).
- **Overwrite confirmation** — prompt the user before overwriting an existing
  file.
- **`decklist save` with name override** — allow
  `decklist save <filepath> as <name>` to set an explicit decklist name that
  differs from the filename stem.
