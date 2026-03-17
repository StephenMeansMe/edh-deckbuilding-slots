# US-014: Resize, delete, and show categories

> **Status**: Pending GitHub Issue creation
> **Label**: `user-story`
> **Branch**: `claude/category-management-features-GYxwO`

---

## User Story

**As an** EDH deckbuilder,
**I want** to resize, delete, and show individual categories,
**so that** I can correct mistakes and focus on parts of my decklist without
restarting the app or manually editing a save file.

## Background

The `category` command already supports `create` and `rename`. The three
operations in this story complete the basic CRUD surface for user-created
categories and add a focused view for a single category.

Related domain rules (see `docs/domain-concepts.md`):
- Fixed categories (Commander, Basic Lands, Companion, Uncategorized) cannot
  be renamed or deleted; the same restriction applies here.
- When a category is deleted, its cards must not be lost — they move to
  Uncategorized (consistent with how `disable-partner` / `disable-background`
  / `disable-companion` evacuate cards).
- Uncategorized is created on first use; the existing `remove_card` /
  evacuation logic handles this already.

## Acceptance Criteria

### category resize

- [ ] `category resize <name> <new-slots>` changes the `total_slots` of an
  existing user-created `CappedCategory`.
- [ ] Fixed categories (Commander, Basic Lands, Companion, Uncategorized)
  reject `resize` with an appropriate error message.
- [ ] If `<new-slots>` is less than the number of cards currently in the
  category, the command is rejected with a clear message (e.g., "Cannot
  resize: category has N card(s); remove cards first or choose a size ≥ N").
- [ ] `<new-slots>` must be a positive integer (1–99); out-of-range values are
  rejected.
- [ ] On success, the command echoes the new size (e.g., "Resized 'Ramp' to
  8 slots.").
- [ ] The change is reflected immediately in subsequent `decklist show`
  output and persists through a save/load cycle.

### category delete

- [ ] `category delete <name>` removes a user-created category from the
  decklist.
- [ ] Fixed categories reject `delete` with an appropriate error message.
- [ ] Cards from the deleted category are moved to Uncategorized.
- [ ] The REPL's persistent "Uncategorized is non-empty" warning is triggered
  if the deleted category held any cards.
- [ ] On success, the command echoes a confirmation (e.g., "Deleted category
  'Ramp'. 6 card(s) moved to Uncategorized.").
- [ ] The deletion persists through a save/load cycle.

### category show

- [ ] `category show <name>` displays the named category: its name, total
  slots, number of filled slots, and the list of cards.
- [ ] Output format is consistent with the per-category block already used in
  `decklist show`.
- [ ] If the category does not exist, an appropriate error is shown.
- [ ] Works for both user-created and fixed categories (read-only; no
  restriction needed here).

## Technical Notes

- Model layer: `Decklist` needs `resize_category(name, new_slots)` and
  `delete_category(name)` methods; `show`/display is a handler-only concern.
- `resize_category` should raise `CategoryError` for fixed categories and
  `SlotError` when `new_slots < len(cards)`.
- `delete_category` should raise `CategoryError` for fixed categories; card
  evacuation follows the same pattern as `disable_companion` (move each card
  to Uncategorized via the existing mechanism).
- `category show` reuses the same formatting logic as the per-category block
  in `handle_decklist_show` — extract a helper if one doesn't already exist.
- New REPL behaviors (`category show`) warrant a scrut test; new model methods
  (`resize_category`, `delete_category`) warrant pytest unit tests.
- Check whether the help text in `handle_category_help` needs updating with
  the three new subcommands; `tests/functional/01-startup.md` asserts full
  `help` output and may need updating.
