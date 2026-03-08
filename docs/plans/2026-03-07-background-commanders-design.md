# Design: Background Commanders (US-009)

**Date:** 2026-03-07
**User story:** As an EDH deckbuilder I want `deckslots` to support Backgrounds so that I can use the tool for my commanders with the Choose a Background mechanic.

---

## Summary

Add `decklist enable-background` (and `decklist disable-background`) mirroring the existing partners implementation. Background expands the Commander category by 1 slot. Partners and Background may both be enabled simultaneously (giving 3 Commander slots). No card-type validation is performed.

Add `decklist disable-partners` symmetrically.

Add a persistent warning when Commander holds more cards than the enabled modes account for.

---

## Models (`models.py`)

- Add `background_enabled: bool = False` to `Decklist`.
- Add `enable_background()`: sets flag to `True`, increments Commander `total_slots` by 1.
- Add `disable_background()`: sets flag to `False`, decrements Commander `total_slots` by 1, moves **all** Commander cards to Uncategorized (creating Uncategorized if it does not exist).
- Add `disable_partners()`: same behaviour as `disable_background()` but for `partners_enabled`.
- Add `commander_overcrowded` property (or method): returns `True` when `len(Commander.cards) > 1 + partners_enabled + background_enabled`.

---

## Commands (`commands.py`)

### New handlers

| Command | Behaviour |
|---|---|
| `decklist enable-background` | Error if no active decklist; call `enable_background()`; return confirmation |
| `decklist disable-background` | Error if no active decklist; call `disable_background()`; return confirmation noting cards moved to Uncategorized |
| `decklist disable-partners` | Error if no active decklist; call `disable_partners()`; return confirmation noting cards moved to Uncategorized |

### Persistent warning

After every command, check `session.decklist.commander_overcrowded`. If `True`, append a warning line to the response (same pattern as the Uncategorized warning):

```
Warning: Commander has more cards than enabled modes allow. Run 'decklist enable-partners' or 'decklist enable-background', or use 'card move' to move extra commanders elsewhere.
```

The warning clears automatically once the condition is resolved.

### Help text

Add to the `decklist` section:
```
  decklist enable-background    Allow a Background commander (Choose a Background mechanic)
  decklist disable-partners     Remove partner mode and move all commanders to Uncategorized
  decklist disable-background   Remove background mode and move all commanders to Uncategorized
```

### Dispatch

Register `("decklist", "enable-background")`, `("decklist", "disable-background")`, and `("decklist", "disable-partners")`.

---

## Save / Load

**Save:** no changes — Commander cards are written under a plain `Commander` heading regardless of mode. `partners_enabled` / `background_enabled` flags are not persisted.

**Load:** ignore any mode tags in the Commander section heading (e.g., `Commander [partners]` is treated as `Commander`). After loading all Commander cards, set Commander `total_slots` to `max(1, len(commander_cards))`. Mode flags start as `False`. If more than 1 Commander card is present, the overcrowded warning fires on the next command, prompting the user to enable the appropriate mode.

This provides backwards compatibility with existing save files that contain `Commander [partners]`.

---

## Export

No changes. Export already writes all Commander cards under the `Commander` heading regardless of slot count.

---

## Testing

### pytest — models
- `enable_background()` increments Commander slots by 1.
- `disable_background()` decrements slots and moves all Commander cards to Uncategorized.
- `disable_partners()` same behaviour.
- Enabling both partners and background gives Commander 3 slots.
- `commander_overcrowded` is `False` when card count ≤ slots; `True` when card count > slots.

### pytest — commands / handlers
- `enable-background` happy path and no-decklist error.
- `disable-partners` / `disable-background` happy paths; Commander cards appear in Uncategorized.
- Persistent warning appears when Commander is overcrowded; clears when resolved.

### pytest — save / load
- Loading a file with 2 Commander cards sets Commander to 2 slots (dynamic allocation).
- Loading a file with `Commander [partners]` heading ignores the tag and dynamically allocates slots.
- Loading a file with 1 Commander card keeps Commander at 1 slot.

### scrut (`tests/functional/12-background.md`)
- `enable-background` happy path; `decklist show` reflects `2/2 slots filled`.
- `disable-partners` with cards present; cards appear in Uncategorized; overcrowded warning gone.
- Both modes active; Commander shows `3` slots.
- Save / load round-trip: overcrowded warning fires on reload; resolved by `enable-background`.
