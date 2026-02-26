# User Story 005: Export a Decklist

## Story

**As an** EDH deckbuilder,
**I want to** export my finished deck as a plain text file with only
`Commander` and `Maindeck` headings, cards listed in `$QUANTITY $CARDNAME`
format,
**so that** I can easily import the list into online tools such as Moxfield or
Archidekt.

## Background

Once a deck is built and categorised, the user needs to share it with external
platforms that do not understand the deckslots category model. The export
command collapses the internal category structure into the two sections these
tools expect: one card in the `Commander` section and everything else in
`Maindeck`.

Export is intentionally **lossy** — category names and slot counts are
discarded. It produces a snapshot for sharing, not for resuming a session.
Session persistence is handled by `decklist save` / `decklist load` (User
Story 004).

## Acceptance Criteria

### `decklist export <filepath>`

1. Writes the current active decklist to `<filepath>` in a
   Moxfield/Archidekt-compatible plain text format.
2. Returns an error if no decklist is active.
3. Returns an error if `<filepath>` cannot be written (bad path, permissions,
   etc.).
4. On success, prints:
   ```
   Exported '<name>' to '<filepath>'.
   ```
5. The export file has exactly two sections: `Commander` and `Maindeck`,
   separated by a blank line.
6. The `Commander` section contains the commander card as `1 <card-name>`. If
   no commander has been assigned, the `Commander` section is written with no
   card lines.
7. The `Maindeck` section contains every card from every non-Commander
   category (including Basic Lands and Uncategorized), with identical card
   names aggregated across all categories.
8. Cards in the `Maindeck` section are sorted alphabetically by card name.
9. Category names and slot counts are not written to the export file.
10. If the destination file already exists it is silently overwritten; no
    confirmation prompt is shown in the MVP.
11. The file extension is not enforced; the user may supply any path (e.g.,
    `my_deck.txt`, `my_deck`).

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

- The `Commander` heading is the bare word `Commander`.
- The `Maindeck` heading is the bare word `Maindeck`.
- Card lines are `<integer quantity> <card name>`.
- The two sections are separated by a single blank line.

### General

12. If the active decklist contains cards in Uncategorized, the persistent
    Uncategorized warning (shown before every command response when
    Uncategorized is non-empty) is displayed as usual — the export operation
    still completes successfully. The Uncategorized cards appear in the
    `Maindeck` section of the export file.

## Notes

- `decklist export` does **not** update the session file
  (`~/.config/deckslots/session`). Exporting a deck is not the same as saving
  a session; use `decklist save` to persist session state.
- An incomplete deck (fewer than 100 cards, or cards remaining in
  Uncategorized) can be exported without error. The persistent Uncategorized
  warning already signals work-in-progress state.
- The export format is designed to round-trip through `decklist import` (User
  Story 002): an exported file can be re-imported and will produce the same
  card assignments as the original `Commander` / `Maindeck` import flow.

## Future Work (out of scope)

- **Export sorting options** — sort `Maindeck` cards by mana value, by type,
  or by the category they came from.
- **Export format variants** — CSV, JSON, or platform-specific formats
  (Archidekt, Manabox, etc.).
- **Overwrite confirmation** — prompt the user before overwriting an existing
  file.
