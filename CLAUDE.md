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

## Development Workflow

No build system, test runner, or linter is configured yet. Update this section as tooling is added.

### Common Commands

```bash
# (placeholder — update once pyproject.toml or equivalent is added)
# python -m pytest           # Run tests
# ruff check .               # Lint
# ruff format .              # Format
# mypy .                     # Type check
```

## Conventions

- **Branch naming**: Feature branches use `claude/` prefix for AI-assisted work.
- **Commits**: Use clear, descriptive commit messages.
- **Python style**: Follow PEP 8. Specific formatter/linter TBD.

## Key Domain Concepts

- **EDH / Commander**: A multiplayer Magic: The Gathering format using 100-card singleton decks led by a legendary creature (the "commander").
- **Slots**: A deckbuilding abstraction where functional roles (e.g., "ramp," "removal," "card draw") are allocated a number of slots, and individual cards fill those slots.

## Notes for AI Assistants

- This is a greenfield project. When adding new files, follow Python packaging best practices (e.g., `src/` layout or flat layout with `pyproject.toml`).
- Prefer modern Python tooling (pyproject.toml over setup.py, Ruff over flake8/black, etc.).
- No CI/CD pipeline is configured yet. Propose one if/when tests or publishing are needed.
- Keep this file updated as the project evolves.
