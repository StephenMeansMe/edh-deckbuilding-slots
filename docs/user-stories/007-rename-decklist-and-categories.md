# User Story 007 – Rename Decklist and Categories

## Summary
As an EDH deckbuilder, I want to be able to rename my decklist and any of the categories I added myself, so that if I change my mind or make a typo I don't have to start all over again.

## Background
Deckbuilding is iterative. Names chosen early in the process often need refinement as a build takes shape. Without a rename command, fixing a typo or changing a category concept requires deleting and recreating the entire category — along with all its assigned cards.

## Acceptance Criteria

### AC 1: Rename the active decklist
`decklist rename` prompts for a new name. On confirmation, the active decklist's display name is updated.

```
deckslots> decklist rename
New name: My Commander Deck
deckslots> Renamed decklist to 'My Commander Deck'.
```

### AC 2: Rename a user-created category
`category rename <name>` identifies the target category (case-insensitive, multi-word), then prompts for the new name.

```
deckslots> category rename my ramp
New name: Ramp Package
deckslots> Renamed category 'My Ramp' to 'Ramp Package'.
```

### AC 3: Fixed categories cannot be renamed
Commander, Basic Lands, and Uncategorized are fixed and cannot be renamed. An error is returned without prompting.

```
deckslots> category rename commander
Cannot rename fixed category 'Commander'.
```

### AC 4: Category not found returns error
If the given name does not match any category, an error is returned immediately (no prompt).

### AC 5: Empty new name is rejected
If the user provides an empty name at the prompt, the rename is cancelled.

```
deckslots> category rename ramp
New name:
Name cannot be empty.
```

### AC 6: Name conflict is rejected
If the new category name conflicts (case-insensitively) with an existing category, the rename is rejected.

```
deckslots> category rename ramp
New name: combo
Category 'combo' already exists.
```

### AC 7: Rename persists on save
After renaming, `decklist save` and `decklist load` preserve the new name.

## Out of Scope
- Renaming fixed categories (Commander, Basic Lands, Uncategorized)
- Changing category slot counts (separate concern)
- Auto-save on rename
