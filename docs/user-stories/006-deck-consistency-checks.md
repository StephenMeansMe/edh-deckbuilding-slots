# User Story 006: Deck Consistency Checks

## Story

**As an** EDH deckbuilder,
**I want** the app to keep me consistent by doing nothing if I try to move a
card into a category where it already is, by not letting me add the same
non-basic-land card into more than one slot anywhere in the deck, and by not
letting me add basic lands anywhere but the "Basic Lands" category,
**so that** I can guarantee a basic consistent structure of my deck without
introducing hard-to-spot errors.

## Background

Three consistency constraints protect the structural integrity of a Commander
deck:

1. **Redundant-move no-op** — moving a card to the category it already
   occupies is a harmless no-op, not an error. This is a usability choice:
   silently succeeding prevents the user from being surprised by error messages
   when re-running the same command.

2. **Singleton non-basic-land rule** — the same non-basic-land card may not
   appear in more than one slot in the entire deck, regardless of which
   categories it spans. The model already enforces this in `Decklist.add_card()`
   for capped categories, but `card move` currently bypasses `add_card` and
   manipulates `category.cards` directly, leaving a gap. This story closes that
   gap for all user-facing commands.

3. **Basic-land restriction** — basic land cards (the 12 names in
   `BASIC_LAND_NAMES`) may only be placed in the "Basic Lands" category. All
   other categories must reject them. Currently only the inverse is enforced:
   the `allowed_cards` whitelist on Basic Lands blocks non-basic-lands from
   entering it. This story adds the symmetric restriction on the other side.

## Acceptance Criteria

### Redundant `card move` — no-op

1. If `card move <card-name> <to-category>` is run and `<card-name>` is already
   in `<to-category>`, the command prints:
   ```
   '<card-name>' is already in '<to-category>'. Nothing to do.
   ```
   and exits successfully (no error prefix, exit code 0).

   This supersedes User Story 003 criterion 6, which called for an error in
   this case.

### Singleton non-basic-land rule on `card move`

2. `card move <card-name> <to-category>` must enforce the singleton rule. If a
   different entry for `<card-name>` already exists somewhere in the deck (in
   any capped category other than the card's current category), the move is
   rejected and the command prints:
   ```
   Error: '<card-name>' is already in the deck (in '<existing-category>').
   ```

3. The check described in criterion 2 is performed **after** confirming the
   card exists and **before** moving it, so the source category is never
   mutated if validation fails.

4. Basic land cards are exempt from the singleton check on move, consistent
   with the existing model behaviour.

### Basic-land restriction on `card add` and `card move`

5. `card add <category> <card-name>` rejects a basic land card if `<category>`
   is not "Basic Lands", printing:
   ```
   Error: Basic lands can only be added to the 'Basic Lands' category.
   ```

6. `card move <card-name> <to-category>` rejects moving a basic land card to
   any category other than "Basic Lands", printing the same error as
   criterion 5.

7. Moving a basic land card from a non-Basic-Lands category (e.g., from
   Uncategorized after it landed there via `card remove`) **to** "Basic Lands"
   is permitted and subject to normal Basic Lands whitelist validation.

## Notes

- The redundant-move no-op (criterion 1) is a behaviour change from User
  Story 003. Any tests asserting an error for "card already in target" must be
  updated to expect the no-op message instead.
- Criteria 5 and 6 only apply to user-facing commands (`card add`, `card
  move`). Internal operations such as `decklist import` and `card remove`
  already route basic lands to the correct category by construction.
- The singleton check in criterion 2 is equivalent to the exclusivity check
  already present in `Decklist.add_card()`. The preferred implementation is to
  route `card move` through `add_card` (or to call the same validation logic)
  rather than manipulating `category.cards` directly, so the check is not
  maintained in two places.
- The `domain-concepts.md` note that `card move` bypasses `add_card` describes
  the current implementation gap that this story closes.

## Future Work (out of scope)

- **`decklist check`** — a command that scans a loaded deck and reports all
  consistency violations at once.
- **Commander singleton rule** — a commander must be a legendary creature;
  validation requires Scryfall integration and is post-MVP.
