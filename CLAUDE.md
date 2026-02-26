# CLAUDE.md

## Project Overview

**edh-deckbuilding-slots** is a Python project for managing Magic: The Gathering EDH (Commander) deckbuilding through a "slots" system.

## Repository Structure

```
edh-deckbuilding-slots/
├── bin/
│   └── deckslots              # Standalone CLI entrypoint
├── docs/
│   ├── ROADMAP.md             # MVP scope, product requirements, roadmap
│   ├── plan.md                # Implementation plan and design decisions
│   └── user-stories/
│       ├── 001-create-decklist-with-categorized-slots.md
│       ├── 002-import-decklist-from-file.md
│       └── 003-card-management.md
├── src/
│   └── deckslots/
│       ├── __init__.py
│       ├── cli.py             # Command parser (ParsedCommand, parse_command)
│       ├── commands.py        # Session state, command handlers, dispatch registry
│       ├── models.py          # Domain models (Category, Decklist)
│       └── repl.py            # Interactive REPL loop
├── tests/
│   ├── __init__.py
│   ├── test_cli.py            # Parser behavior tests (pytest)
│   ├── test_commands.py       # Handler and dispatch tests (pytest)
│   ├── test_models.py         # Domain model tests (pytest)
│   └── functional/            # Functional CLI tests (scrut)
│       ├── setup.md           # Smoke test / bootstrap
│       ├── 01-startup.md      # Startup, quit/exit, help
│       ├── 02-decklist.md     # decklist create/show
│       ├── 03-categories.md   # category create/list
│       ├── 04-cards.md        # card add/move/remove/delete
│       ├── 05-uncategorized.md # Uncategorized warning system
│       ├── 06-save-load.md    # decklist save/load
│       └── 07-autoload.md     # Auto-resume and recovery mode
├── .gitignore
├── CLAUDE.md
├── pyproject.toml             # Project metadata, deps, tool config
└── uv.lock                    # Locked dependencies
```

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

### Setup

```bash
uv sync                      # Install all dependencies (creates .venv)
```

#### Install scrut (one-time — functional CLI testing framework)

```bash
# Download prebuilt binary (Linux x86_64)
curl -L https://github.com/facebookincubator/scrut/releases/download/v0.4.3/scrut-v0.4.3-linux-x86_64.tar.gz \
  | tar -xz -C /tmp/ && mv /tmp/scrut-linux-x86_64/scrut ~/.local/bin/scrut && chmod +x ~/.local/bin/scrut

# Alternatively: cargo install scrut
```

### Common Commands

```bash
uv run pytest                # Run unit/integration tests (193 tests)
uv run pytest -x             # Stop on first failure (useful during Red phase)
uv run pytest -v             # Verbose output
uv run pytest --tb=short     # Concise tracebacks
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run ty check              # Type check
uv run deckslots             # Run the app (console script)
./bin/deckslots              # Run the app (standalone script)

# Functional CLI tests (run from project root)
scrut test --work-directory . tests/functional/              # All functional tests
scrut test --work-directory . tests/functional/01-startup.md # One file
uv run pytest && scrut test --work-directory . tests/functional/  # Full suite
```

## Conventions

- **Branch naming**: Feature branches use `claude/` prefix for AI-assisted work.
- **Commits**: Use clear, descriptive commit messages. Prefix with `test:`, `feat:`, `fix:`, or `refactor:` to reflect the TDD phase.
- **Merging PRs**: Use squash merge (`gh pr merge <n> --squash --delete-branch`). After merging, reset local `main` to the pre-session commit (`git reset --hard <sha>`) so feature work lives only on the squash commit.
- **Creating PRs**: Must be on the feature branch when running `gh pr create` — running it from `main` errors with "head branch is the same as base branch."
- **Python style**: Follow PEP 8, enforced by Ruff (E, F, I, W rule sets).
- **Line length**: Ruff enforces 88 characters. Long f-string error messages and multi-argument test helper calls are common offenders — wrap early to avoid a separate refactor commit.
- **Test organization**: Mirror the source tree under a `tests/` directory (e.g., `src/slots/deck.py` → `tests/test_deck.py`). Test files are prefixed with `test_`, test functions with `test_`.
- **Test naming**: Use descriptive names that state the expected behavior, e.g., `test_deck_rejects_duplicate_cards`, not `test_deck_1`.

## Key Domain Concepts

- **EDH / Commander**: A multiplayer Magic: The Gathering format using 100-card singleton decks led by a legendary creature (the "commander").
- **Slot**: A single position in a decklist that expects to have a card associated with it. A slot is instantiated *before* any card is assigned to it (i.e., an empty slot is valid).
- **Category**: A named grouping of slots (e.g., "Ramp," "Removal," "Draw"). User-created categories are *capped* (1–99 slots). Categories can also be *uncapped* (0+ slots, no upper limit), used for Basic Lands.
- **Fixed category**: A category with a special structural role in the deck, created automatically by `Decklist.create()`. The Commander category (1 fixed slot) and the Basic Lands category (0 starting slots, uncapped) are both mandatory.  *(Roadmap: partner, background, and companion are optional pre-configured fixed slots.)*
- **Basic Lands**: A fixed, uncapped category restricted to the 12 valid basic land names (5 classics, Wastes, 6 snow-covered) via `allowed_cards`. Unlike normal categories, Basic Lands allows duplicate card names and has no upper slot limit. The `allowed_cards` whitelist is enforced by `Decklist.add_card()`.
- **Exclusivity**: In the MVP, categories and slots are *exclusive* — a card occupies exactly one slot in one category. *(Roadmap: when exclusivity is toggled off, a card may appear in multiple slots/categories, but must have a designated **primary** category slot. The app distinguishes primary vs. non-primary appearances. Non-exclusive mode allows the total slot count to exceed 100.)*

## MVP Scope

- **One commander slot** — exactly 1 mandatory fixed slot in its own category.
- **Basic Lands category** — mandatory fixed category, uncapped (0+ slots), restricted to 12 basic land names, allows duplicates.
- **Exclusive categories only** — each card occupies exactly one slot in one category; total slots = 100.
- **CLI on Linux** — local-only, no remote deployment.
- **Flat text file I/O** — `$QUANTITY $CARDNAME` format (e.g., `1 Sol Ring`).
- **No semantic validation** — the app does not validate card types against category names.

For detailed product requirements, roadmap, and user stories, see `docs/`.

## Notes for AI Assistants

- **TDD is mandatory.** Do not skip the Red phase. Always start by writing or showing the failing test before implementing production code.
- **Test split**: pytest covers unit and integration tests (parser, models, handlers). scrut covers functional/black-box CLI tests (`tests/functional/*.md`). New REPL behaviors should get a scrut test; new handler/model behaviors get a pytest test.
- **scrut test format**: Each ` ```scrut ` code block is one test case with exactly one `$ ` command (the first line). All subsequent lines are expected stdout. Use separate blocks for setup steps (setup block has no expected output). `$TMPDIR` is shared within a file but fresh per file; use subdirectories (`$TMPDIR/t1`, etc.) to isolate test cases that write save files. Run with `scrut test --work-directory . tests/functional/`.
- **Test file imports**: Only import names that already exist in production code. A top-level `ImportError` fails the *entire* test file, not just the new test class. Add new imports to test files at the same TDD step you add the production function.
- This is a greenfield project. When adding new files, follow Python packaging best practices (e.g., `src/` layout or flat layout with `pyproject.toml`).
- Prefer modern Python tooling (pyproject.toml over setup.py, Ruff over flake8/black, etc.).
- No CI/CD pipeline is configured yet. Propose one if/when tests or publishing are needed.
- Use `uv run` to execute commands within the project's virtual environment.
- Use `uv add` / `uv add --dev` to manage dependencies.
- When asked to add a feature, the first response should be a test, not an implementation.
- Keep commits granular: one commit per TDD step (red, green, refactor).
- Keep this file updated as the project evolves.
- **Documentation**: end-user documentation lives in the GitHub repo wiki — do not create local Markdown files for user-facing content. Developer and AI assistant documentation (architecture, plans, conventions) lives as Markdown files in the repo (`CLAUDE.md`, `docs/`).
