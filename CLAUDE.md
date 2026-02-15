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
- **Slot**: A single position in a decklist that expects to have a card associated with it. A slot is instantiated *before* any card is assigned to it (i.e., an empty slot is valid).
- **Category**: A named grouping of one or more slots (e.g., "Ramp," "Removal," "Draw"). Categories are configured by the user with 1–99 slots each.
- **Fixed slot**: A slot with a special structural role in the deck. The commander slot (with its own category) is mandatory. Partner, background, and companion are optional pre-configured fixed slots.
- **Exclusivity**: By default, categories and slots are *exclusive* — a card occupies exactly one slot in one category. When exclusivity is toggled off, a card may appear in multiple slots/categories, but must have a designated **primary** category slot. The app distinguishes primary vs. non-primary appearances. Non-exclusive mode allows the total slot count to exceed 100.

## Product Requirements

### Deployment

- This is a local-only application. It will **not** be deployed to a remote server or exposed to the Internet.

### Decklist Export

- **Required**: Export a decklist to a **plain text file**.
- **Optional**: Export a decklist to a **CSV file**.

### Validation

- The MVP does **not** enforce semantic validation on slots. For example, placing a sorcery card in a "Lands" slot or an invalid commander in the commander slot will **not** raise an error.
- When Scryfall integration is enabled, the app **should warn** if:
  - A card is not found in the Scryfall database.
  - A card is found but is not legal in the Commander format.

### Scryfall Integration

- The app **may** pull card information from the [Scryfall API](https://scryfall.com/docs/api) as an enrichment layer (art, oracle text, legality, etc.).
- Scryfall data is **not required** to add or remove cards from a decklist. The core decklist operations must work offline / without API access.
- When enabled, Scryfall integration provides **warnings** (not errors) for unrecognized or format-illegal cards. These warnings do not block the user from building their deck.

### Decklist Structure

- Every decklist has a **mandatory fixed slot** (with its own category) for the **commander**.
- Optional pre-configured fixed slots: **partner**, **background**, **companion**.
- User-configured categories may have **1–99 slots** each.
- **Exclusive mode (default)**: Each card appears in exactly one slot in one category. Total slots = 100.
- **Non-exclusive mode**: A card may appear in multiple category slots but must have one **primary** slot. The app visually distinguishes primary vs. secondary appearances. Total slots may exceed 100.

### Pre-configured Categories

The app may ship with optional starter categories such as:

- Lands
- Ramp
- Removal
- Draw
- Enablers
- Payoffs

These are suggestions the user can adopt, modify, or ignore.

## Notes for AI Assistants

- **TDD is mandatory.** Do not skip the Red phase. Always start by writing or showing the failing test before implementing production code.
- This is a greenfield project. When adding new files, follow Python packaging best practices (e.g., `src/` layout or flat layout with `pyproject.toml`).
- Prefer modern Python tooling (pyproject.toml over setup.py, Ruff over flake8/black, etc.).
- No CI/CD pipeline is configured yet. Propose one if/when tests or publishing are needed.
- When asked to add a feature, the first response should be a test, not an implementation.
- Keep commits granular: one commit per TDD step (red, green, refactor).
- Keep this file updated as the project evolves.
