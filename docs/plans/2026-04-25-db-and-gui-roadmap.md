# Roadmap: Database + GUI Integration

Order of work for shipping the database backend
([2026-04-25-database-storage-design.md](2026-04-25-database-storage-design.md))
and the PySide6 GUI ([2026-04-25-gui-pyside6-design.md](2026-04-25-gui-pyside6-design.md))
without regressing the CLI.

## Why this ordering

Both features depend on the same two refactors: a **service layer**
(extract domain operations from `commands.py` handlers) and a **repository
seam** (`DecklistRepository` protocol). Doing those once, up front, means the
DB and GUI work doesn't double up on plumbing.

## Phases

### Phase 0 — Shared refactors

- **0.1** Extract `services.py` returning `CommandResult` / `DomainEvent`.
  CLI handlers become 2–3 line adapters.
- **0.2** Introduce `DecklistRepository` protocol in `storage.py` with a
  `PlaintextRepository` wrapping the current `_format_save_file` /
  `_parse_save_file`. Route `handle_decklist_save` / `handle_decklist_load`
  through it.
- **0.3** Gate: full pytest + scrut suites pass; zero user-visible change.

### Phase 1 — SQLite backend

- **1.1** `SqliteRepository` + schema migrations (see database design doc).
- **1.2** Legacy `decklist.bak` import on first SQLite launch.
- **1.3** Multi-deck CLI commands: `decklist list`, `decklist switch <name>`,
  `decklist delete <name>`.
- **1.4** `storage_backend = "sqlite"` opt-in via `config.json`; default stays
  `"plaintext"`.

Exit: power users can maintain a deck library; plaintext import/export still
round-trips through Moxfield.

### Phase 2 — GUI MVP ✅

- **2.1** ✅ PySide6 shell, deck board view, menu bar, repository-backed deck open.
- **2.2** ✅ Drag-and-drop wired to `services.can_drop` / `services.move_card`,
  with full validation feedback.
- **2.3** ✅ Scryfall image pipeline (async fetch, on-disk cache, placeholder).
- **2.4** ✅ Ship behind `[project.optional-dependencies] gui`. CLI install stays
  slim.

Exit: `deckslots gui` opens any deck the CLI can; drag-drop maintains all
existing invariants.

### Phase 3 — Quality of life

- **3.1** Deck-library sidebar (uses `repository.list()`). ✅ Shipped in Phase 2/4.
- **3.2** Card search/typeahead from the Scryfall index, drag-from-search. → [#103](https://github.com/StephenMeansMe/edh-deckbuilding-slots/issues/103)
- **3.3** Undo/redo built on a `DomainEvent` log persisted in a new `events`
  table. → [#104](https://github.com/StephenMeansMe/edh-deckbuilding-slots/issues/104)
- **3.4** Mana-curve / color-identity panel (cheap once cards are in SQL). → [#105](https://github.com/StephenMeansMe/edh-deckbuilding-slots/issues/105)

### Phase 4 — Hardening ✅

Detailed plan: [2026-05-13-phase4-hardening-plan.md](2026-05-13-phase4-hardening-plan.md).

- **4.0** ✅ GUI shipping completeness — SQLite-always backend, Add Category /
  New Deck / Import / Export dialogs, Scryfall first-run background worker.
- **4.1** ✅ Ordered SQLite migrations with forward-version safety (US-022).
- **4.2** ✅ PyInstaller spec, AppImage script, font-bundling loader,
  platformdirs cross-platform paths, GitHub Actions release workflow.
- **4.3** ✅ Performance pass — disk-hit throttle skip, shared network
  throttle, `bench_cold_open.py` harness (US-021). Local 100-card cold open
  measured at 80 ms; warm at 43 ms (targets < 2 s / < 500 ms).
- **4.4** ✅ Accessibility — Shift+M keyboard-only Move Card, accessible
  names on tiles / inspector / status bar, Commander legality warnings
  surfaced in the status bar (US-019).
- **4.5** ✅ Architecture docs synced with Phase 3 modules (US-020).

## Decisions to confirm before Phase 1

1. Default storage backend stays `plaintext` (lower risk) — Phase 1 is opt-in.
2. Multi-deck CLI commands ship in Phase 1; the GUI is **not** the only
   multi-deck UX.
3. Scryfall image cache lives next to the existing oracle_cards cache under
   `$XDG_CACHE_HOME/deckslots/`.

## End-to-end verification

- **After Phase 0**: `uv run pytest` + `scrut test tests/functional/` green.
- **After Phase 1**: REPL → `decklist save` → `sqlite3 library.db .dump` shows
  expected rows → `decklist load` → `decklist export` → file imports cleanly
  into Moxfield.
- **After Phase 2**: deck created in the REPL opens in the GUI; drag a card,
  quit the GUI, reopen in the REPL; the move is reflected and plaintext export
  is byte-identical except for the moved card.
- **After Phase 3**: 100-card deck with images opens cold in < 2 s, warm cache
  in < 500 ms.

## Critical file map

| Concern | New | Modified |
|---|---|---|
| Service layer | `src/deckslots/services.py`, `src/deckslots/events.py` | `src/deckslots/commands.py` (handlers shrink) |
| Storage | `src/deckslots/storage.py` | `src/deckslots/commands.py:44–148`, `src/deckslots/repl.py:81–115`, `src/deckslots/config.py` |
| Scryfall images | — | `src/deckslots/scryfall.py` |
| GUI | `src/deckslots/gui/*` | `src/deckslots/cli.py` (gui subcommand), `pyproject.toml` (optional-deps) |
| Tests | `tests/test_services.py`, `tests/test_storage_repository.py`, `tests/gui/*` | existing `test_commands.py` tests rewire onto services |
