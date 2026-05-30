---
name: run-tests
description: Use when running or interpreting tests for edh-deckbuilding-slots. Covers the two-framework split, single-file invocations, worktree caveat, and scrut format rules.
---

# Run Tests

The project uses **two test frameworks** that must both pass before any commit.

## Full Suite

```bash
uv run pytest && scrut test --work-directory . tests/functional/
```

Run this from the **main project directory** (see worktree caveat below).

## pytest (unit/integration)

```bash
uv run pytest                                                                     # all tests
uv run pytest -x                                                                  # stop on first failure (Red phase)
uv run pytest tests/test_models.py                                                # single file
uv run pytest tests/test_commands.py::TestDecklistEnableCompanion                 # single class
uv run pytest tests/test_commands.py::TestDecklistEnableCompanion::test_returns_confirmation  # single test
```

## pytest-qt (GUI tests)

```bash
QT_QPA_PLATFORM=offscreen uv run pytest tests/gui/    # headless (required in CI; works locally)
uv run pytest tests/gui/                              # with a real display (local only)
```

GUI tests live in `tests/gui/`. Each module starts with `pytest.importorskip("PySide6")` and skips cleanly if the `[gui]` extra is not installed. Install it with `uv sync --extra gui`.

## scrut (functional / black-box REPL)

```bash
scrut test --work-directory . tests/functional/                    # all scenarios
scrut test --work-directory . tests/functional/13-companion.md     # single file
```

`--work-directory .` must point to the project root (the directory containing `pyproject.toml`).

## Worktree Caveat

If you are in a git worktree (`.worktrees/<branch>/`), **run pytest from the main project directory**, not the worktree — `uv` cache writes fail inside worktrees.

```bash
# Wrong — uv cache write fails:
cd .worktrees/my-branch && uv run pytest

# Correct — always from the main project directory:
uv run pytest
```

The `_deckslots.pth` file at `.venv/lib/python3.12/site-packages/_deckslots.pth` must point to the **worktree's** `src/` while developing, and be restored to the main `src/` after PR creation:

```bash
# While developing on a worktree branch, point .pth to the worktree:
echo "$(git rev-parse --show-toplevel)/.worktrees/<branch>/src" \
  > .venv/lib/python3.12/site-packages/_deckslots.pth

# After PR merge, restore to main src/:
echo "$(git rev-parse --show-toplevel)/src" \
  > .venv/lib/python3.12/site-packages/_deckslots.pth
```

## Linting and Type Checking

Run before any PR:

```bash
uv run ruff check .
uv run ruff format .
uv run ty check
```

## scrut Format Quick Reference

- Each ` ```scrut ` block has exactly **one** `$ ` command (first line); all remaining lines are expected stdout
- Use `$TMPDIR` subdirectories to isolate test cases that write save files
- `$TMPDIR` is **not** expanded in expected output — filter variable paths with `| grep -v "pattern"`
- When adding any new command, update `tests/functional/01-startup.md` (it asserts the full `help` output)

## What Each Framework Covers

| Framework | Tests |
|-----------|-------|
| pytest | Unit and integration: models, handlers, parsers |
| pytest-qt | GUI widget behavior (requires `[gui]` extra; skips if PySide6 absent) |
| scrut | Black-box REPL scenarios: full command flows, save/load round-trips |
