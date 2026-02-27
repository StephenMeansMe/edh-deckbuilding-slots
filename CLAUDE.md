# CLAUDE.md

## Project Overview

**edh-deckbuilding-slots** is a Python project for managing Magic: The Gathering EDH (Commander) deckbuilding through a "slots" system.

## Repository Structure

- `bin/` — Standalone CLI entrypoint
- `docs/` — ROADMAP, user stories, domain-concepts.md, implementation plans
- `src/deckslots/` — Source: cli.py, models.py, commands.py, repl.py
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

The app uses an **object-verb command pattern** with a dispatch registry:

- **`cli.py`** — `parse_command(line)` returns a `ParsedCommand` with `kind` (`builtin`, `object_verb`, `unknown`, `empty`), `obj`, `verb`, and `args`. Known objects: `decklist`, `category`, `card`. Builtins: `quit`, `exit`, `help`.
- **`models.py`** — Domain models. `Category` (name, total_slots, fixed, capped, allowed_cards, cards) and `Decklist` (name, categories dict). `Decklist.create()` auto-adds mandatory Commander and Basic Lands categories. `BASIC_LAND_NAMES` is a module-level `frozenset[str]` of all 12 valid basic land names. `Category.cards` is `list[str]` (allows duplicates for basic lands). `Decklist.add_card(card, category_name)` enforces: category existence, `allowed_cards` whitelist, fullness, and singleton exclusivity across capped categories (uncapped categories skip the exclusivity check). Capped categories validate `1 <= total_slots <= 99`; uncapped categories validate `total_slots >= 0` with no upper limit. Uncapped categories return `None` for `available` and `False` for `is_full`.
- **`commands.py`** — `Session` holds REPL state (`decklist: Decklist | None`). Handler functions (e.g., `handle_decklist_create`) return strings. Two arg-resolution helpers: `_resolve_category_and_card(args, categories)` uses greedy longest-prefix match to resolve multi-word category names from `<category> <card>` args (used by `card add`); `_resolve_card_and_category_suffix(args, categories)` uses greedy longest-suffix match to resolve multi-word category names from `<card> <category>` args (used by `card move`). Card move/remove operations manipulate `category.cards` directly in the handlers rather than through model methods, so the exclusivity check in `Decklist.add_card()` is not re-run during a move. `register_all_handlers(session)` builds a `dict[tuple[str, str], Callable]` dispatch registry. `dispatch(cmd, registry)` routes commands.
- **`repl.py`** — `run_repl()` creates a Session and registry, loops on `input()`, delegates to dispatch for object-verb commands and `handle_help` for the help builtin.

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

- **Branch naming**: Feature branches use `claude/` prefix for AI-assisted work.
- **Commits**: Use clear, descriptive commit messages. Prefix with `test:`, `feat:`, `fix:`, or `refactor:` to reflect the TDD phase.
- **Merging PRs**: Use squash merge (`gh pr merge <n> --squash --delete-branch`). After merging, reset local `main` to the pre-session commit (`git reset --hard <sha>`) so feature work lives only on the squash commit.
- **Creating PRs**: Must be on the feature branch when running `gh pr create` — running it from `main` errors with "head branch is the same as base branch."
- **Python style**: Follow PEP 8, enforced by Ruff (E, F, I, W rule sets); line length 88 characters.
- **Test organization**: Mirror the source tree under a `tests/` directory. Test files are prefixed with `test_`, test functions with `test_`.
- **Test naming**: Use descriptive names that state the expected behavior, e.g., `test_deck_rejects_duplicate_cards`, not `test_deck_1`.

## Key Domain Concepts

See [`docs/domain-concepts.md`](docs/domain-concepts.md) for the full glossary (slots, categories, fixed categories, basic lands, exclusivity, Uncategorized, and card-add business rules). Read it before planning any feature that touches business logic.

## Notes for AI Assistants

- **Read all user stories and `docs/domain-concepts.md` before planning.** Files under `docs/user-stories/` are the authoritative spec; new stories are added as the project grows.
- **TDD is mandatory.** Do not skip the Red phase. Always start by writing the failing test before implementing production code.
- **Test split**: pytest covers unit and integration tests (parser, models, handlers). scrut covers functional/black-box CLI tests (`tests/functional/*.md`). New REPL behaviors should get a scrut test; new handler/model behaviors get a pytest test.
- **scrut test format**: Each ` ```scrut ` block has exactly one `$ ` command (the first line); all subsequent lines are expected stdout. Use `$TMPDIR` subdirectories to isolate test cases that write save files. Run with `scrut test --work-directory . tests/functional/`.
- **Test file imports**: Only import names that already exist in production code. A top-level `ImportError` fails the *entire* test file.
- Use `uv run` to execute commands; `uv add` / `uv add --dev` to manage dependencies.
- Keep this file updated as the project evolves.
- **Documentation**: end-user documentation lives in the GitHub repo wiki. Developer and AI assistant documentation lives as Markdown files in the repo (`CLAUDE.md`, `docs/`).
