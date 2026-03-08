# User Story 008: Partner Commanders

## Story

**As an** EDH deckbuilder,
**I want** `deckslots` to support partner commanders,
**so that** I can brew decklists with those cards.

## Acceptance Criteria

- `decklist enable-partners` expands the Commander category from 1 slot to 2 slots.
- The command can only be used when a decklist is active; if no decklist is active, the app shows an error.
- Partners mode is reflected in `decklist show`: the Commander category displays `2/2 slots filled` when both slots are occupied.
- Partners mode survives a save/load round-trip: after saving and reloading, the Commander category still has 2 slots and both commanders are present.
- `decklist export` lists both commanders in the `Commander` section of the exported file.
- Help text includes `decklist enable-partners`.
