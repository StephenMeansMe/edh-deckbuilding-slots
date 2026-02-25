# User Story 003: Card Management — Move, Remove, and Delete

## Story

**As an** EDH deckbuilder,
**I want to** move cards between categories, remove a card from its category back
to an Uncategorized holding area, and permanently delete cards from the decklist,
**so that** I can refine my deck without starting over.

## Background

Once a decklist is populated (whether by `card add` or `decklist import`), the
user needs to reorganise cards as their thinking evolves. Three distinct
operations cover the full lifecycle:

- **Move** — reassign a card that already belongs to a category to a different
  one (no holding area involved).
- **Remove** — "unassign" a card from its category without deleting it; the card
  lands in the Uncategorized holding area and the app nags the user to re-assign
  it.
- **Delete** — permanently remove a card from the decklist; it is not placed
  anywhere.

The Uncategorized holding area is fixed, uncapped, and not directly user-addable.
It is created by `decklist import` (User Story 002) and can also be created on
demand by `card remove` when it does not yet exist.

## Acceptance Criteria

### `card move <card-name> <to-category>`

1. Moves the named card from wherever it currently lives to `<to-category>`.
2. Returns an error if the card is not in the decklist.
3. Returns an error if `<to-category>` does not exist.
4. Returns an error if `<to-category>` is capped and has no available slots.
5. Returns an error if `<to-category>` is Uncategorized (not directly
   user-addable — use `card remove` instead).
6. Returns an error if the card is already in `<to-category>`.
7. Successfully moves a card FROM Uncategorized to a capped category that has
   available slots.
8. On success, prints:
   ```
   Moved '<card-name>' from '<from-category>' to '<to-category>'.
   ```
9. Multi-word card names are supported; argument parsing uses greedy
   longest-suffix matching to resolve the target category (e.g.,
   `card move Atraxa, Praetors' Voice Ramp` correctly identifies `Ramp` as the
   target and `Atraxa, Praetors' Voice` as the card name).

### `card remove <card-name>`

10. Removes the named card from its current category and places it in the
    Uncategorized holding category.
11. If the Uncategorized category does not yet exist, it is created automatically
    (fixed, uncapped, `user_addable=False`) before the card is added.
12. Returns an error if the card is not in the decklist.
13. Returns an error if the card is already in Uncategorized; suggests using
    `card delete` to permanently remove it.
14. On success, prints:
    ```
    Removed '<card-name>' from '<from-category>'. Card is now in Uncategorized.
    ```
15. After the operation, the persistent Uncategorized warning (already
    implemented in the REPL from User Story 002) activates or increments.
16. Multi-word card names are supported; all remaining args after `remove` are
    joined as the card name.

### `card delete <card-name>`

17. Permanently removes the named card from the decklist, regardless of which
    category it occupies (including Uncategorized).
18. Returns an error if the card is not in the decklist.
19. On success, prints:
    ```
    Deleted '<card-name>' from the decklist.
    ```
20. Does NOT place the card in Uncategorized; the card is gone entirely.
21. Multi-word card names are supported (same as `card remove`).

### General

22. All three commands require an active decklist; return an error if none is
    active.
23. The persistent Uncategorized warning (shown before every command response
    when Uncategorized is non-empty) is unaffected by `card move` and `card
    delete` — it remains active as long as Uncategorized is non-empty. After
    `card remove` the count in the warning increments.

## Notes

- `card move` is the primary mechanism for emptying Uncategorized after an
  import: the user moves each card to its intended category.
- `card remove` is intentionally a "soft" operation. Cards accumulate in
  Uncategorized and the persistent nag encourages the user to act.
- `card delete` is intentionally destructive. No confirmation prompt is shown
  in the MVP — the user typed the command.
- `card move` does **not** pass through an exclusivity check for the source
  category when performing the move (the card is removed from the source before
  being added to the target, so no duplicate-in-decklist violation can arise).
  All other `add_card` validations — `allowed_cards` whitelist, slot capacity —
  still apply.
- The Uncategorized category created by `card remove` is identical in structure
  to the one created by `decklist import`: fixed, uncapped, `user_addable=False`.
  They are treated as the same category by the REPL.
- `card remove` on a basic land in the Basic Lands category is permitted; the
  land moves to Uncategorized (it is no longer in the `allowed_cards`-restricted
  category). Moving it back out of Uncategorized via `card move` requires
  targeting Basic Lands, which will enforce the `allowed_cards` whitelist.

## Future Work (out of scope)

- **Bulk move** — `card move all <to-category>` or move all Uncategorized cards
  at once.
- **Undo / history** — reverse the last operation.
- **Conflict detection** — warn before `card delete` when the card is the only
  occupant of a fixed category slot (e.g., deleting the commander).
