# Tests

## Test Split

- **pytest** — unit and integration tests: parser, models, command handlers (`tests/test_*.py`)
- **scrut** — functional/black-box CLI tests: full REPL input/output scenarios (`tests/functional/*.md`)

New REPL behaviors should get a scrut test; new handler/model behaviors get a pytest test.

## Test Organization

- Mirror the source tree: `tests/test_cli.py` covers `src/deckslots/cli.py`, etc.
- File names: `test_<module>.py`; function names: `test_<expected_behavior>` (e.g. `test_deck_rejects_duplicate_cards`, not `test_deck_1`)
- Only import names that already exist in production code — a top-level `ImportError` fails the **entire** test file.

## scrut Format

Each ` ```scrut ` block has exactly one `$ ` command (the first line); all remaining lines are expected stdout:

````markdown
```scrut
$ deckslots --help
Usage: ...
```
````

Key rules:
- Use `$TMPDIR` subdirectories to isolate test cases that write save files.
- `$TMPDIR` is **not** expanded in expected output — filter variable-path lines with `| grep -v "pattern"` (e.g. `Exported '...' to '...'`).
- When adding new commands, update `tests/functional/01-startup.md` — it asserts the full `help` output.
- Run with `scrut test --work-directory . tests/functional/` from the project root.
