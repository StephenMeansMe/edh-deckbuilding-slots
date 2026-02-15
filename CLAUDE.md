# CLAUDE.md

## Project Overview

**edh-deckbuilding-slots** is a Python project for managing Magic: The Gathering EDH (Commander) deckbuilding through a "slots" system. The project is in its initial scaffolding phase.

## Repository Structure

```
edh-deckbuilding-slots/
├── .gitignore          # Python-focused gitignore
└── CLAUDE.md           # This file
```

The project has no source code yet. Structure will be updated as modules are added.

## Tech Stack

- **Language**: Python
- **Package management**: TBD (`.gitignore` supports pipenv, Poetry, PDM, UV, pixi)
- **Testing**: TBD (`.gitignore` supports pytest, tox, nox, nose, hypothesis)
- **Type checking**: TBD (`.gitignore` supports mypy, Pyre, pytype)
- **Linting**: TBD (`.gitignore` supports Ruff)
- **Documentation**: TBD (`.gitignore` supports Sphinx, mkdocs)

## Development Methodology: Test-Driven Design (TDD)

This project follows **strict TDD**. Every change must go through the Red-Green-Refactor cycle:

1. **Red** — Write a failing test that defines the desired behavior.
2. **Green** — Write the minimum production code to make the test pass.
3. **Refactor** — Clean up the code while keeping all tests green.

### TDD Rules

- **Never write production code without a failing test.** If there is no test demanding the code, the code should not exist.
- **Write only enough of a test to fail.** A compilation/import error counts as a failure — don't write more test code than necessary to get the first failure.
- **Write only enough production code to pass the failing test.** Resist the urge to generalize ahead of the tests.
- **Refactor only when tests are green.** Keep refactoring steps small and re-run tests after each change.
- **Tests are first-class code.** Keep them readable, well-named, and maintained. Delete tests only when they are genuinely redundant.

### Workflow for Every Change

```
1. Write a failing test          → commit (test: ...)
2. Make it pass (minimal code)   → commit (feat/fix: ...)
3. Refactor if needed            → commit (refactor: ...)
4. Repeat
```

Each step should be its own commit so the TDD history is visible in the git log.

## Development Workflow

No build system, test runner, or linter is configured yet. Update this section as tooling is added.

### Common Commands

```bash
# (placeholder — update once pyproject.toml or equivalent is added)
# python -m pytest           # Run tests
# python -m pytest -x        # Stop on first failure (useful during Red phase)
# python -m pytest --tb=short # Concise tracebacks
# ruff check .               # Lint
# ruff format .              # Format
# mypy .                     # Type check
```

## Conventions

- **Branch naming**: Feature branches use `claude/` prefix for AI-assisted work.
- **Commits**: Use clear, descriptive commit messages. Prefix with `test:`, `feat:`, `fix:`, or `refactor:` to reflect the TDD phase.
- **Python style**: Follow PEP 8. Specific formatter/linter TBD.
- **Test organization**: Mirror the source tree under a `tests/` directory (e.g., `src/slots/deck.py` → `tests/test_deck.py`). Test files are prefixed with `test_`, test functions with `test_`.
- **Test naming**: Use descriptive names that state the expected behavior, e.g., `test_deck_rejects_duplicate_cards`, not `test_deck_1`.

## Key Domain Concepts

- **EDH / Commander**: A multiplayer Magic: The Gathering format using 100-card singleton decks led by a legendary creature (the "commander").
- **Slots**: A deckbuilding abstraction where functional roles (e.g., "ramp," "removal," "card draw") are allocated a number of slots, and individual cards fill those slots.

## Notes for AI Assistants

- **TDD is mandatory.** Do not skip the Red phase. Always start by writing or showing the failing test before implementing production code.
- This is a greenfield project. When adding new files, follow Python packaging best practices (e.g., `src/` layout or flat layout with `pyproject.toml`).
- Prefer modern Python tooling (pyproject.toml over setup.py, Ruff over flake8/black, etc.).
- No CI/CD pipeline is configured yet. Propose one if/when tests or publishing are needed.
- When asked to add a feature, the first response should be a test, not an implementation.
- Keep commits granular: one commit per TDD step (red, green, refactor).
- Keep this file updated as the project evolves.
