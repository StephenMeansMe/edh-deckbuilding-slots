# CLAUDE.md

## Project Overview

**edh-deckbuilding-slots** is a Python project for managing Magic: The Gathering EDH (Commander) deckbuilding through a "slots" system.

## Repository Structure

- `bin/` — Standalone CLI entrypoint
- `docs/` — ROADMAP, domain-concepts.md, plans/, design/
- `docs/design/` — GUI design handoff: hi-fi prototype (`Big Bridge Energy.html`), wireframes, screenshots, and [`design-handoff.md`](docs/design/design-handoff.md) (full spec)
- `src/deckslots/` — Source modules + CLAUDE.md (architecture, command grammar, design decisions) + `data/templates/` (built-in template assets)
- `tests/` — pytest unit/integration tests + scrut functional CLI tests (`tests/functional/`); see [tests/CLAUDE.md](tests/CLAUDE.md)

## Tech Stack

- **Language**: Python 3.12+
- **Package management**: [uv](https://docs.astral.sh/uv/)
- **Build backend**: [Hatchling](https://hatch.pypa.io/) (src/ layout)
- **Testing**: [pytest](https://docs.pytest.org/)
- **Linting/Formatting**: [Ruff](https://docs.astral.sh/ruff/)
- **Type checking**: [ty](https://github.com/astral-sh/ty)
- **CLI/output**: [click](https://click.palletsprojects.com/) (output via `click.echo`/`click.style`; interactive prompts via `click.prompt`)

## Architecture

See [`src/deckslots/CLAUDE.md`](src/deckslots/CLAUDE.md) for module-level architecture, command grammar, domain model, and design decisions.

## Development Methodology: TDD

This project follows **strict TDD** (Red-Green-Refactor). Every change must follow this commit sequence:

```
1. Write a failing test          → commit (test: ...)
2. Make it pass (minimal code)   → commit (feat/fix: ...)
3. Refactor if needed            → commit (refactor: ...)
```

Never write production code without a failing test (import errors count).

## Development Workflow

```bash
uv sync                      # Install all dependencies (creates .venv)
uv sync --extra gui          # Also install optional GUI dependencies (PySide6)
uv run pytest                # Run unit/integration tests
uv run pytest -x             # Stop on first failure (useful during Red phase)
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run ty check              # Type check
uv run deckslots             # Run the app (console script)
./bin/deckslots              # Run the app (standalone script)

scrut test --work-directory . tests/functional/  # Functional CLI tests
```

> **First run:** `uv run deckslots` will prompt to download Scryfall oracle data (~70 MB, network required). The cache lives at `$XDG_CACHE_HOME/deckslots/oracle_cards.json` and is reused on subsequent runs (max age: 7 days).

## Conventions

- **Branch naming**: New features, fixes, and docs changes **must always be implemented on a new feature branch** — never directly on `main`. Branch names use the `claude/` prefix (e.g. `claude/companion-slot`, `claude/export-encoding`).
- **Commits**: Use clear, descriptive commit messages. Prefix with `test:`, `feat:`, `fix:`, or `refactor:` to reflect the TDD phase.
- **Merging PRs**: Use squash merge (`gh pr merge <n> --squash --delete-branch`). After merging, reset local `main` to the pre-session commit (`git reset --hard <sha>`) so feature work lives only on the squash commit.
- **Creating PRs**: Must be on the feature branch — `gh pr create` from `main` errors with "head branch is the same as base branch."
- **Python style**: PEP 8, enforced by Ruff (E, F, I, W); line length 88.

## Forbidden git operations

These operations are **categorically banned** — no exceptions, no "safe probe" use cases:

| Banned command | Why banned | Safe alternative |
|----------------|-----------|-----------------|
| `git stash` / `git stash pop` | Stash pop can fail on concurrent file changes (e.g. `uv.lock`), leaving work in an unrecoverable state | `git show HEAD:<path> \| uv run ruff check -` to lint the committed version; `git diff HEAD -- <path>` to see what changed |
| `git reset --hard` | Discards uncommitted work permanently | `git stash` is banned, but `git restore <path>` is OK for single-file revert when you've confirmed the file is expendable |
| `git push --force` to `main`/`master` | Overwrites shared history | Never force-push to main; force-push only to personal feature branches, and only with explicit user instruction |

**Project enforcement:**
- `.claude/settings.json` contains a `PreToolUse` hook that intercepts any Bash command matching `git stash` and exits 2 (blocked).
- `.git/config` contains a `stash` alias that prints the prohibition and exits 1 (shell-level fallback).
- Neither guard is committed to the repo — note them in dev setup if this project gains new contributors.

**At session start:** Re-read this section before any git operations. The rule is categorical: if you are tempted to use a banned command, find the safe alternative listed above instead.

## Key Domain Concepts

See [`docs/domain-concepts.md`](docs/domain-concepts.md) for the full glossary (slots, categories, fixed categories, basic lands, exclusivity, Uncategorized, and card-add business rules). Read it before planning any feature that touches business logic.

## GUI Design Reference

The GUI target design lives in [`docs/design/`](docs/design/):
- **[`design-handoff.md`](docs/design/design-handoff.md)** — full design spec: screens, interactions, state shape, design tokens, typography, spacing. **Read this before implementing any GUI work.**
- **`Big Bridge Energy.html`** — hi-fi interactive prototype (open in a browser; no build step). This is the visual target.
- **`EDH Deckbuilding Slots - Wireframes.html`** — lo-fi layout exploration (context only; Option A / Masonry was selected).
- **`screenshots/`** — light/dark themes, omnibar, and wireframe overview PNGs.

## Notes for AI Assistants

- **GitHub Issues are the authoritative source for implementation status.** Open = pending; closed = shipped. Before planning any feature, check for an existing issue:
  ```bash
  gh issue list --label user-story --state all   # list all user stories
  gh issue list --state open                     # all open work (bugs + stories)
  gh issue view <N>                              # read a specific issue
  ```
  New user stories must be created as GitHub Issues before implementation begins — see `.claude/skills/new-user-story.md` for the format. Do not create new files in `docs/plans/` for tracking feature status; create a GitHub Issue instead.
- **`docs/plans/` files are historical design references**, not a status board. They document the design decisions and TDD plans that guided past implementations. Their status is reflected in the linked GitHub Issues and merged PRs, not in the files themselves. Read them for architectural context; do not treat them as a to-do list.
- **TDD is mandatory.** Do not skip the Red phase. Always start by writing the failing test before implementing production code.
- **Project skills** — project-local procedures invoked via the Skill tool or `/skill-name` in Claude Code. Available in `.claude/skills/`: `new-user-story` (GitHub Issue format), `implement-decklist-mode` (Partner/Background/Companion pattern), `add-repl-command` (handler + 01-startup.md update), `run-tests` (pytest + scrut invocations, worktree caveat), `bump-version` (all locations to update when cutting a release), `merge-pr` (squash merge + local main reset).
- **Testing details** (test split, scrut format, naming conventions): see [`tests/CLAUDE.md`](tests/CLAUDE.md).
- Use `uv run` to run commands; `uv add` / `uv add --dev` to manage dependencies.
- Keep this file and its sub-`CLAUDE.md` files updated as the project evolves.
- **Commit lint/type fixes incrementally.** When fixing ruff or ty errors across a gate check, commit after each fixable batch (auto-fix, then manual fixes) so that a failed revert cannot undo all in-progress work.
