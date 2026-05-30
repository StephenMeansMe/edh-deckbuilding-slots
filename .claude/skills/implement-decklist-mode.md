---
name: implement-decklist-mode
description: Use when adding a new Commander mode (partner-style or companion-style) to edh-deckbuilding-slots. Covers model layer, command handlers, REPL warnings, save/load, and export/import changes.
---

# Implement a New Decklist Mode

A project-local skill for implementing a new Commander mode following strict TDD. Use this for any feature that adds an `enable-X` / `disable-X` pair — Partners, Background, Companion, and future equivalents.

## When to Use

- Adding a new `decklist enable-X` / `decklist disable-X` command pair
- Adding a new fixed category managed by enable/disable lifecycle

## Before You Start

### Answer these domain questions first

Read `docs/domain-concepts.md` and answer before writing any code:

- [ ] Is this a **slot expansion** (adds to `Commander.total_slots` like Partner/Background) or a **separate category** (creates a new `CappedCategory` like Companion)?
- [ ] What does `disable_X()` do when cards are present? (Evacuate to Uncategorized)
- [ ] What is the REPL warning condition? (Should be a new `@property` on `Decklist`)
- [ ] What is the save format heading? (Plain word — `Companion`, not `Companion [1 slots]`)
- [ ] Does the **export** format emit a new section? If yes, where? (Companion: between Commander and Maindeck)
- [ ] Does this affect singleton exclusivity? (`UncappedCategory` is exempt; `CappedCategory` is not)

### Check for an open user story

```bash
gh issue list --label user-story --state open
```

If none exists for this mode, use the `new-user-story` skill first.

---

## Phases to Skip

If this mode has **no REPL warning condition** (no persistent `@property` that triggers a warning) and **no new save-format section**, Phases 3 and 4 can be skipped. Slot-expansion modes that only grow the Commander category (future partner variants) often fit this pattern. Companion-style modes — which create a separate fixed category with their own save/export section and REPL warning — need all four phases.

---

## Phase 1 — Model Layer (TDD)

### Step 1: Write failing pytest

Add a test class to `tests/test_models.py` covering:
- `enable_X()` sets the flag and updates the model correctly
- `disable_X()` clears the flag and evacuates cards to Uncategorized
- The new computed `@property` (e.g., `companion_slot_empty`)
- Error cases (calling `enable_X()` when already enabled)

Use `CappedCategory` or `UncappedCategory` in fixtures — never abstract `Category`.

```bash
uv run pytest tests/test_models.py -x
```

Expected: `AttributeError` — the methods do not exist yet.

### Step 2: Commit (Red)

```
test: failing tests for enable_X / disable_X / X_property
```

### Step 3: Implement in `src/deckslots/models.py`

- Add `X_enabled: bool = False` field to `Decklist`
- Add `enable_X()` and `disable_X()` methods
- Add computed `@property`
- If creating a separate category: `CappedCategory("X", 1, fixed=True)`

```bash
uv run pytest tests/test_models.py -x
```

### Step 4: Commit (Green)

```
feat: enable_X / disable_X / X_enabled on Decklist
```

---

## Phase 2 — Command Handlers (TDD)

### Step 5: Write failing pytest

Add test class to `tests/test_commands.py`. Import handler names **at the top of the file** — an `ImportError` at module level is a valid Red signal.

```bash
uv run pytest tests/test_commands.py -x
```

Expected: `ImportError` on the new handler names.

### Step 6: Commit (Red)

```
test: failing tests for handle_decklist_enable_X / disable_X
```

### Step 7: Implement in `src/deckslots/commands.py`

- Add `handle_decklist_enable_X(session, cmd)` and `handle_decklist_disable_X(session, cmd)`
- Register both in `register_all_handlers()` under `("decklist", "enable-X")` and `("decklist", "disable-X")`
- Add both to the help string in `handle_help()`

```bash
uv run pytest tests/test_commands.py -x
```

### Step 8: Commit (Green)

```
feat: handle_decklist_enable_X / disable_X + dispatch registration
```

---

## Phase 3 — REPL Warning, Save/Load, Export/Import

### Step 9: Add REPL warning (`src/deckslots/repl.py`)

Add to the persistent warning block after every dispatch:

```python
if session.decklist is not None and session.decklist.X_property:
    click.echo("Warning: ...")
```

### Step 10: Update save/load (`src/deckslots/storage.py`; re-exported from `commands.py`)

- `_format_save_file`: emit the section heading and cards when mode is enabled
- `_parse_save_file`: recognise the heading; restore the flag and category

### Step 11: Update export/import (`src/deckslots/commands.py`) — only if mode has an export-visible section

- `_format_export_file`: emit the section in the correct position
- `_parse_import_file`: recognise the heading; route cards and enable the mode

---

## Phase 4 — Functional Tests

### Step 12: Write scrut scenarios

Create `tests/functional/NN-X-mode.md` covering:
- `enable-X` happy path (category appears in `decklist show`)
- `enable-X` without active decklist (error message)
- `disable-X` evacuates cards to Uncategorized
- Save/load round-trip preserves mode state
- Export/import round-trip restores mode (if applicable)

### Step 13: Update `tests/functional/01-startup.md` — MANDATORY

The help output scenario asserts the exact full `help` text. Any change to `handle_help()` breaks this. Add the two new commands in the correct position (alphabetical within the `decklist` group).

### Step 14: Run the full suite

```bash
uv run pytest && scrut test --work-directory . tests/functional/
```

### Step 15: Commit

```
feat: REPL warning, save/load, export/import, and functional tests for X mode
```

---

## Quick Reference

| Phase | Files |
|-------|-------|
| Model | `src/deckslots/models.py`, `tests/test_models.py` |
| Handlers | `src/deckslots/commands.py`, `tests/test_commands.py` |
| REPL warning | `src/deckslots/repl.py` |
| Save/load | `src/deckslots/storage.py` (`_format_save_file`, `_parse_save_file`; re-exported from `commands.py`) |
| Export/import | `src/deckslots/commands.py` (`_format_export_file`, `_parse_import_file`) |
| Functional tests | `tests/functional/NN-X-mode.md`, `tests/functional/01-startup.md` |

## Notes

- Domain glossary and category rules → `docs/domain-concepts.md`
- Dispatch mechanics, `ParsedCommand` fields → `src/deckslots/CLAUDE.md`
- User story format → `new-user-story` skill
- `move_card()` must NOT call `add_card()` internally — avoids spurious exclusivity failure while the card is still in the source category
