# CLAUDE.md

## Project Overview

**edh-deckbuilding-slots** is a Python project for managing Magic: The Gathering EDH (Commander) deckbuilding through a "slots" system.

## Repository Structure

- `bin/` — Standalone CLI entrypoint
- `docs/` — ROADMAP, domain-concepts.md, implementation plans
- `src/deckslots/` — Source modules (cli.py, models.py, commands.py, repl.py) + CLAUDE.md (architecture notes)
- `tests/` — pytest unit/integration tests + scrut functional CLI tests (`tests/functional/`)

## Tech Stack

- **Language**: Python 3.12+
- **Package management**: [uv](https://docs.astral.sh/uv/)
- **Build backend**: [Hatchling](https://hatch.pypa.io/) (src/ layout)
- **Testing**: [pytest](https://docs.pytest.org/)
- **Linting/Formatting**: [Ruff](https://docs.astral.sh/ruff/)
- **Type checking**: [ty](https://github.com/astral-sh/ty)
- **Documentation**: GitHub repo wiki (end-user docs); Markdown files in repo (developer and AI assistant docs)

## Architecture

See [`src/deckslots/CLAUDE.md`](src/deckslots/CLAUDE.md) for module-level architecture notes.

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

```bash
uv sync                      # Install all dependencies (creates .venv)
uv run pytest                # Run unit/integration tests
uv run pytest -x             # Stop on first failure (useful during Red phase)
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run ty check              # Type check
uv run deckslots             # Run the app (console script)
./bin/deckslots              # Run the app (standalone script)

# Functional CLI tests (run from project root)
scrut test --work-directory . tests/functional/              # All functional tests
uv run pytest && scrut test --work-directory . tests/functional/  # Full suite
```

## Conventions

- **Branch naming**: New features, fixes, and docs changes **must always be implemented on a new feature branch** — never directly on `main`. Branch names use the `claude/` prefix (e.g. `claude/companion-slot`, `claude/export-encoding`).
- **Commits**: Use clear, descriptive commit messages. Prefix with `test:`, `feat:`, `fix:`, or `refactor:` to reflect the TDD phase.
- **Merging PRs**: Use squash merge (`gh pr merge <n> --squash --delete-branch`). After merging, reset local `main` to the pre-session commit (`git reset --hard <sha>`) so feature work lives only on the squash commit.
- **Creating PRs**: Must be on the feature branch when running `gh pr create` — running it from `main` errors with "head branch is the same as base branch."
- **Python style**: Follow PEP 8, enforced by Ruff (E, F, I, W rule sets); line length 88 characters.
- **Test organization**: Mirror the source tree under a `tests/` directory. Test files are prefixed with `test_`, test functions with `test_`.
- **Test naming**: Use descriptive names that state the expected behavior, e.g., `test_deck_rejects_duplicate_cards`, not `test_deck_1`.

## Key Domain Concepts

See [`docs/domain-concepts.md`](docs/domain-concepts.md) for the full glossary (slots, categories, fixed categories, basic lands, exclusivity, Uncategorized, and card-add business rules). Read it before planning any feature that touches business logic.

## Notes for AI Assistants

- **User stories live as GitHub Issues** (label: `user-story`) on `StephenMeansMe/edh-deckbuilding-slots`. Before planning any feature, fetch the relevant stories:
  ```bash
  gh issue list --label user-story --state all   # list all stories
  gh issue view <N>                               # read a specific story
  ```
  `docs/domain-concepts.md` remains the authoritative domain glossary; read it before planning any feature that touches business logic. New user stories must be created as GitHub Issues before implementation begins — see `.claude/skills/new-user-story.md` for the format.
- **TDD is mandatory.** Do not skip the Red phase. Always start by writing the failing test before implementing production code.
- **Test split**: pytest covers unit and integration tests (parser, models, handlers). scrut covers functional/black-box CLI tests (`tests/functional/*.md`). New REPL behaviors should get a scrut test; new handler/model behaviors get a pytest test.
- **scrut test format**: Each ` ```scrut ` block has exactly one `$ ` command (the first line); all subsequent lines are expected stdout. Use `$TMPDIR` subdirectories to isolate test cases that write save files. Run with `scrut test --work-directory . tests/functional/`. When adding new commands, also update `tests/functional/01-startup.md` (it asserts the full `help` output). `$TMPDIR` is not expanded in scrut expected output — use `| grep -v "pattern"` to filter variable-path lines (e.g. `Exported '...' to '...'`).
- **Test file imports**: Only import names that already exist in production code. A top-level `ImportError` fails the *entire* test file.
- Use `uv run` to execute commands; `uv add` / `uv add --dev` to manage dependencies.
- Keep this file updated as the project evolves.
- **Documentation**: end-user documentation lives in the GitHub repo wiki. Developer and AI assistant documentation lives as Markdown files in the repo (`CLAUDE.md`, `docs/`).
