---
name: add-repl-command
description: Use when adding a new object-verb REPL command to edh-deckbuilding-slots. Covers handler registration, help text, and the mandatory 01-startup.md update.
---

# Add a New REPL Command

A project-local skill for adding a new `<object> <verb>` command following strict TDD.

## When to Use

- Adding any new command such as `category resize`, `card list`, `template apply`
- Any change that adds a line to the output of `help`

## Before You Start

Identify before writing any code:

- [ ] What are the object and verb? (e.g., `category` / `resize`)
- [ ] Does the command need new model methods on `Decklist` or `Category`? If yes, run Phase 0 first.
- [ ] Does it require a new entry in `handle_help()`? (Almost always yes — triggers `01-startup.md` update)

---

## Phase 0 — Model Changes (only if needed)

Write failing pytest in `tests/test_models.py` → commit `test: ...`
Implement in `src/deckslots/models.py` → commit `feat: ...`

---

## Phase 1 — Handler (TDD)

### Step 1: Write failing scrut scenario

Add a scenario to the appropriate `tests/functional/NN-topic.md` (create a new file if none fits). This test will fail until implementation is complete — that is the point.

### Step 2: Write failing pytest for the handler

Add a test class to `tests/test_commands.py`. Import the handler name **at the top of the file** — an `ImportError` at module level is a valid Red signal.

```bash
uv run pytest tests/test_commands.py -x
```

Expected: `ImportError` on the new handler name.

### Step 3: Commit (Red)

```
test: failing tests for handle_<object>_<verb>
```

### Step 4: Implement the handler

In `src/deckslots/commands.py`:
- Add `handle_<object>_<verb>(session, cmd)` returning a `str`
- Register in `register_all_handlers()` under `("<object>", "<verb>")`
- Add to the help string in `handle_help()`

```bash
uv run pytest tests/test_commands.py -x
```

### Step 5: Commit (Green)

```
feat: handle_<object>_<verb> + dispatch registration
```

---

## Phase 2 — Help Text and Documentation — MANDATORY

### Step 6: Update `tests/functional/01-startup.md`

**This step is mandatory and easy to forget.** The `help` scenario asserts the exact full help output. Any change to `handle_help()` breaks this test.

Update the expected output to include the new command in the correct position (alphabetical within its object group: `card`, `category`, `decklist`, `template`).

### Step 7: Update command grammar table

In `src/deckslots/CLAUDE.md`, add a row to the correct command table under the appropriate `### X commands` section.

---

## Phase 3 — Full Suite

### Step 8: Run the full suite

```bash
uv run pytest && scrut test --work-directory . tests/functional/
```

If `01-startup.md` fails, the help string in `handle_help()` and the scrut expected output are out of sync — fix both together.

### Step 9: Commit

```
feat: <object> <verb> command — handler, help text, 01-startup.md, grammar table
```

---

## Quick Reference

| Step | File |
|------|------|
| Scrut scenario | `tests/functional/NN-topic.md` |
| Handler + dispatch + help | `src/deckslots/commands.py` |
| Handler tests | `tests/test_commands.py` |
| Help output assertion | `tests/functional/01-startup.md` ← MANDATORY |
| Grammar table | `src/deckslots/CLAUDE.md` |

## Notes

- Dispatch mechanics, `ParsedCommand` fields, command grammar → `src/deckslots/CLAUDE.md`
- If the command adds a new mode lifecycle (`enable-X` / `disable-X`) → use the `implement-decklist-mode` skill instead
- Argument parsing: `card add` uses longest-prefix match for category; `card move` uses longest-suffix match — do not assume positional args
