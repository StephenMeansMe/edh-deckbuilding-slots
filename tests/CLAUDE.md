# Tests

## Test Split

- **pytest** — unit and integration tests: parser, models, command handlers (`tests/test_*.py`)
- **pytest + pytest-qt** — GUI tests in `tests/gui/*.py`. Each module starts with `pytest.importorskip("PySide6")` so they skip cleanly when the optional `[gui]` extra is not installed.
- **scrut** — functional/black-box CLI tests: full REPL input/output scenarios (`tests/functional/*.md`)

New REPL behaviors should get a scrut test; new handler/model behaviors get a pytest test; new GUI widget behavior gets a `tests/gui/test_*.py` with the `qtbot` fixture.

## Test Organization

- Mirror the source tree: `tests/test_cli.py` covers `src/deckslots/cli/parser.py`, `tests/test_commands.py` covers `src/deckslots/cli/commands.py`, etc.
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
- Scrut files are named `NN-topic.md` (two-digit sequence, e.g. `01-startup.md`, `13-companion.md`). Add new files at the end of the sequence; do not renumber existing files.

## GUI tests (Phase 2)

- Live in `tests/gui/`. Each module starts with `pytest.importorskip("PySide6")`.
- Use the `qtbot` fixture from `pytest-qt`. Register widgets via `qtbot.addWidget(w)` so they are torn down cleanly between tests.
- **Headless CI**: set `QT_QPA_PLATFORM=offscreen` in the environment (Qt cannot create a real display in CI containers). Locally: `QT_QPA_PLATFORM=offscreen uv run pytest tests/gui/`.
- Prefer testing model/state behavior over render output — e.g. assert `tile.would_accept_drop(mime)` rather than relying on Qt's drag-source machinery. Drag/drop integration end-to-end is covered by `services.can_drop` unit tests in the model layer.

## Scryfall in tests

Tests that exercise Scryfall-touching code must either mock `scryfall.lookup_card` (using `unittest.mock.patch`) or disable validation entirely (`is_validation_enabled=False`) to avoid live network calls. Never make real Scryfall HTTP requests in tests.
