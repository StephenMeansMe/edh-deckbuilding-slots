# Plan: Phase 4 — Hardening

Detailed implementation plan for Phase 4 of the DB + GUI roadmap
([2026-04-25-db-and-gui-roadmap.md](2026-04-25-db-and-gui-roadmap.md)).

Phase 4 covers three areas called out in the roadmap — packaging, a performance
pass, and accessibility — plus a GUI completeness gate and schema hardening that
must land first. Every step follows strict TDD (Red → Green → Refactor).

## Incorporated open issues

| Issue | Title | Phase 4 section |
|-------|-------|-----------------|
| #83 (US-017) | Create a new deck from the GUI | 4.0.3 |
| #85 (US-019) | Warn when cards violate Commander legality / banlist | 4.4.3 |
| #86 (US-020) | Keep architecture docs in sync with implemented modules | 4.5.1 |
| #87 (US-021) | Verify and enforce the cold-open performance target | 4.3 |
| #88 (US-022) | Define a schema migration path for SQLite beyond v1 | 4.1 |

**Excluded issues** (scope would deviate from Phase 4 hardening):

| Issue | Reason |
|-------|--------|
| #75 (US-016) | Multi-session REPL is a large Phase 3-sized feature; deferred |
| #84 (US-018) | Drag-to-reorder categories is a new interaction feature, not hardening |

---

## Phase 4.0 — GUI shipping completeness

Before distributing a binary the GUI must be a self-contained deckbuilding tool.
A user who installs `deckslots[gui]` and launches `deckslots gui` for the first
time should be able to create, import, export, and organise decks without
touching the REPL. Five gaps from the 2026-05-13 gap review each have a design
doc written; this phase closes them all.

### 4.0.1 — SQLite always-on for the GUI

**Design doc**: `2026-05-13-sqlite-default-gui.md`

`run_app()` currently picks a backend via `config.get_storage_backend()`, which
can return `PlaintextRepository`. The deck-library panel has no meaningful use
with a single-file backend. The GUI must always use `SqliteRepository`.

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_app.py`: assert `run_app()` constructs `SqliteRepository` without reading `config.get_storage_backend()` |
| Green | `src/deckslots/gui/app.py`: remove `_pick_repository()` call; hard-code `SqliteRepository()` |

**Exit**: `deckslots gui` with `{"storage_backend": "plaintext"}` in config still
opens `SqliteRepository`; REPL path is unaffected.

---

### 4.0.2 — Add Category dialog

**Design doc**: `2026-05-13-add-category-gui.md`

The `+ Category` toolbar button is a no-op. Without it users cannot create
categories from the GUI.

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_main_window.py`: empty name → OK disabled; duplicate name → error label visible; valid input → `services.create_category` called, `deck_mutated` emitted |
| Green | `src/deckslots/gui/main_window.py`: new `_AddCategoryDialog(QDialog)` with `QLineEdit` + `QSpinBox`; wire `+ Category` action in `DeckWindow._on_add_category` |

**Exit**: `+ Category` in the toolbar creates a visible tile; duplicate and
empty names are rejected inline before OK is pressed.

---

### 4.0.3 — Create new deck from the GUI (US-017 / #83)

The `New` toolbar button and `File → New Deck…` are no-ops. A first-time GUI
user cannot create a deck without the REPL.

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_main_window.py`: `New` action → dialog opens; valid name → `Decklist.create()` called, `repository.save()` called, board resets; cancel → deck unchanged; duplicate name → OK disabled |
| Green | `src/deckslots/gui/main_window.py`: new `_NewDeckDialog(QDialog)` (one `QLineEdit`; reuse validation pattern from `_AddCategoryDialog`); wire `File → New Deck…` and toolbar `New` button to `DeckWindow._on_new_deck`; call `Decklist.create(name)`, `repo.save(deck)`, reload board |

**Note**: `_NewDeckDialog` and `_AddCategoryDialog` share a name-validation
pattern; extract a `_NameDialog` base class only if duplication becomes a
maintenance burden — three lines of shared code is not premature abstraction.

**Exit**: `File → New Deck…` creates a new empty deck (Commander + Basic Lands
tiles), auto-saves it to the library, and shows it in `DeckLibraryPanel`.

---

### 4.0.4 — Import / Export file dialogs

**Design doc**: `2026-05-13-gui-import-export.md`

`Import…` and `Export…` toolbar buttons are no-ops. A packaged binary has no
command line for file paths.

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_main_window.py`: patch `QFileDialog.getSaveFileName` → file written, status bar shows export message; patch `QFileDialog.getOpenFileName` → deck replaced, `repo.save()` called; patch `_parse_import_file` to raise → `QMessageBox.warning` shown, deck unchanged |
| Green | `src/deckslots/gui/main_window.py`: `_on_export` and `_on_import` handlers; wire toolbar actions; reuse `_format_export_file` / `_parse_import_file` from `commands.py` unchanged |

**Exit**: round-trip — export a deck, mutate the exported file, re-import — board
reflects the mutation and a Moxfield copy-paste round-trip is byte-compatible.

---

### 4.0.5 — Scryfall first-run background download

**Design doc**: `2026-05-13-scryfall-first-run-gui.md`

On a fresh install the oracle card cache is absent. The GUI silently gives no
card images, no omnibar results, and no indication anything is wrong.

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_app.py`: `is_cache_stale` → True → `_ScryfallWorker` submitted, status bar shows "Updating card index…"; `is_cache_stale` → False with index → `on_scryfall_ready` called synchronously; worker success → `signals.finished` emits dict; worker failure → `signals.failed` emits string |
| Green | `src/deckslots/gui/app.py`: new `_ScryfallWorker(QRunnable)` + `_WorkerSignals(QObject)`; wire `run_app()` to check `is_cache_stale` and start the worker; `src/deckslots/gui/main_window.py`: `on_scryfall_ready`, `on_scryfall_failed` slots; `src/deckslots/gui/board_widget.py`: `set_scryfall_index` forwarded to `ImageLoader` and `Omnibar` |

**Exit**: `deckslots gui` launched cold (no cache) shows "Updating card index…"
in the status bar; after download completes card images and omnibar search work
without restarting the app.

---

### Phase 4.0 exit criterion

`deckslots gui` from a clean XDG temp directory supports the full
create-build-import-export workflow without any REPL interaction. All
`tests/gui/` and `tests/functional/17-gui.md` scrut cases pass.

---

## Phase 4.1 — SQLite schema hardening (US-022 / #88)

`_migrate()` currently applies the entire v1 schema unconditionally with no
forward-migration strategy. Any future schema change will silently break existing
databases or require manual steps a general user cannot perform.

### 4.1.1 — Ordered upgrade list

| TDD step | What to write |
|----------|---------------|
| Red | `tests/test_storage_repository.py`: fresh DB → `schema_version` == 1; DB pre-seeded at version 0 (no schema) → upgrade applies; DB already at current version → no DDL executed (use a spy on `conn.execute`) |
| Green | `src/deckslots/storage.py`: refactor `_migrate(conn)` into a list of `(target_version, upgrade_fn)` pairs; apply only upgrades whose `target_version > stored_schema_version`; each `upgrade_fn(conn)` runs in a transaction and rolls back on failure |

### 4.1.2 — Forward-version safety

| TDD step | What to write |
|----------|---------------|
| Red | `tests/test_storage_repository.py`: DB pre-seeded with `schema_version = 9999` → `SqliteRepository()` raises a clear error (e.g., `RuntimeError("Database schema version 9999 is newer than this app supports (1)")`) |
| Green | `src/deckslots/storage.py`: after reading `schema_version`, compare against `CURRENT_SCHEMA_VERSION` constant; raise if `stored > current` |

### 4.1.3 — Migration design note

Add `docs/plans/2026-05-13-sqlite-migrations.md` documenting the upgrade-list
pattern so future contributors know how to add a v2 schema change. This is a
documentation-only commit (`docs:` prefix).

**Exit**: a DB from schema v1 opens cleanly; a hypothetical future v2 DB
(schema_version = 2) raises a readable error on v1 app; migration tests in CI.

---

## Phase 4.2 — Packaging

**Design doc**: `2026-05-13-packaging-phase4.md`

Ship distributable binaries for Windows, macOS, and Linux so users without
Python can install and run `deckslots gui`.

### 4.2.1 — Font bundling

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_styles.py`: call `apply_theme(app, "light")` with a real `QApplication`; assert `"DM Sans"` in `QFontDatabase.families()` |
| Green | Download `DM_Sans[opsz,wght].ttf` (SIL OFL) to `src/deckslots/data/fonts/`; add `_load_dm_sans()` to `styles.py` using `importlib.resources`; call it at the top of `apply_theme()` |

### 4.2.2 — platformdirs cross-platform paths

| TDD step | What to write |
|----------|---------------|
| Red | Parametrize existing path tests in `tests/test_config.py`, `tests/test_storage_repository.py`, `tests/test_scryfall.py` to assert the path comes from `platformdirs` rather than raw XDG env-var string joins |
| Green | `uv add platformdirs>=4.0`; replace manual `os.environ.get("XDG_…")` + `Path.home()` blocks in `config.py`, `storage.py`, `scryfall.py` with `user_config_dir`, `user_state_dir`, `user_data_dir`, `user_cache_dir` from `platformdirs` |

`platformdirs` goes in core dependencies (not `[gui]`-only) because it benefits
the CLI on macOS (`~/Library/…` paths) too.

### 4.2.3 — PyInstaller spec

New file `packaging/deckslots.spec` (see design doc for full spec). Key points:

- `datas = collect_data_files("deckslots")` — picks up `data/templates/` and `data/fonts/`
- `hiddenimports = ["deckslots.gui"]` — guards against lazy-import stripping
- `console=False` on Windows (REPL not available from binary; acceptable)
- `onefile=True`

Local smoke test (not gated in CI until 4.2.5):
```
uv run pyinstaller packaging/deckslots.spec --distpath dist/
dist/deckslots --help
QT_QPA_PLATFORM=offscreen dist/deckslots gui
```

### 4.2.4 — AppImage (Linux)

New script `packaging/build-appimage.sh` + supporting assets:
- `packaging/deckslots.desktop`
- `packaging/deckslots-256.png` (icon)

The script: PyInstaller `--onedir` → AppDir structure → `appimagetool`. See
design doc for the full script.

### 4.2.5 — GitHub Actions release CI

New file `.github/workflows/release.yml` triggered on `push: tags: ["v*.*.*"]`.

Three build jobs (ubuntu-latest, windows-latest, macos-latest), each:
1. `uv sync --extra gui`
2. `uv run pyinstaller packaging/deckslots.spec`
3. On Linux: `bash packaging/build-appimage.sh`
4. Upload artifact

A final `release` job downloads all artifacts and creates a GitHub Release via
`softprops/action-gh-release@v2`.

Smoke-test step in each job: `dist/deckslots --help` and
`QT_QPA_PLATFORM=offscreen dist/deckslots gui` (fail-fast if the binary
segfaults or exits non-zero).

**Exit**: pushing `v0.2.0` tag triggers the workflow; three binaries appear on the
GitHub Release page within ~15 minutes; each binary passes its smoke test.

---

## Phase 4.3 — Performance (US-021 / #87)

The Phase 3 exit criterion states: "100-card deck with images opens cold in < 2 s,
warm cache in < 500 ms." This has never been measured. `ImageLoader` sleeps 100 ms
per fetch sequentially; 100 images × 100 ms = 10+ seconds worst-case.

### 4.3.1 — Benchmark harness

New file `tests/gui/bench_cold_open.py` (not a pytest test; run manually or in
a dedicated CI step):

```python
import time
from PySide6.QtWidgets import QApplication
from deckslots.gui.app import run_app

os.environ["QT_QPA_PLATFORM"] = "offscreen"
app = QApplication([])
t0 = time.perf_counter()
run_app(exec_loop=False)   # deck load + image scheduling + first paint
elapsed = time.perf_counter() - t0
print(f"Cold open: {elapsed:.3f}s")
```

The benchmark distinguishes cold-cache (no on-disk images) from warm-cache (all
images on disk) by clearing / leaving `$XDG_CACHE_HOME/deckslots/card_images/`.

### 4.3.2 — Parallel image fetching

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_image_loader.py`: submitting N cache-miss requests schedules N concurrent `_FetchTask` runnables (mock `QThreadPool.start` and count calls); a cache-hit request emits `image_ready` without going through `QThreadPool` and without the 100 ms sleep |
| Green | `src/deckslots/gui/image_loader.py`: remove the top-of-`run()` 100 ms sleep for on-disk cache hits (disk read needs no rate-limit delay); keep the 100 ms sleep only for actual Scryfall network fetches. The `QThreadPool.globalInstance()` already runs tasks concurrently — ensure `maxThreadCount` is not capped to 1 |

The Scryfall rate-limit guidance is one request per 100 ms across all
concurrent workers — use a shared `threading.Semaphore` or `threading.BoundedSemaphore`
to enforce this across threads rather than sleeping unconditionally per task.

### 4.3.3 — Verify targets

After the fix, run `bench_cold_open.py` on the reference machine and record
results in the PR description. Both targets must be met before this step closes:
- Cold-cache (no on-disk images): < 2 s (note: this means the app is _usable_
  within 2 s; images may still be loading asynchronously in the background)
- Warm-cache (all images on disk): < 500 ms

If targets are still not met, investigate: lazy image load (schedule only visible
tiles), reduced FIFO cache size, or offscreen rendering profiling.

**Exit**: `bench_cold_open.py` results documented in the PR; both targets met or
a follow-up issue opened with profiling data.

---

## Phase 4.4 — Accessibility

### 4.4.1 — Keyboard-only card move

The design calls out "keyboard-only drag alternative" as a Phase 4 item. The
target UX:

- A card row in `CatTile` can be focused via Tab.
- Pressing `Shift+M` (or a discoverable shortcut shown in the `Card` menu) on a
  focused card opens a small popup or `QInputDialog` listing category names; the
  user selects a destination and presses Enter.
- The move routes through `services.move_card` identically to drag-and-drop, so
  all invariants are enforced.

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_category_tile.py`: a `CatTile` card row is focusable (tabstop); pressing the keyboard shortcut with a card focused triggers the category-picker dialog |
| Green | `src/deckslots/gui/category_tile.py`: set `setFocusPolicy(Qt.StrongFocus)` on card rows; connect `Card → Move Card…` menu item and `Shift+M` shortcut to `DeckWindow._on_keyboard_move`; `_on_keyboard_move` shows a `QInputDialog.getItem` with category names; on accept calls `services.move_card` and emits `deck_mutated` |

### 4.4.2 — Screen-reader labels

| TDD step | What to write |
|----------|---------------|
| Red | `tests/gui/test_category_tile.py` and `tests/gui/test_board_widget.py`: assert that key widgets have non-empty `accessibleName()` / `accessibleDescription()` |
| Green | Set `setAccessibleName` / `setAccessibleDescription` on: `CatTile` header (category name + slot count), card rows (card name + mana cost), `CardInspector` (currently displayed card name), status bar segments, `UncatSidebar` header |

### 4.4.3 — Commander legality / banlist warnings (US-019 / #85)

This fits accessibility-adjacent "hardening" and is scoped to a non-blocking
warning, not a gate.

`services.add_card()` already accepts `scryfall_index`. Extend it to check
`legalities.commander` and append a legality warning to `CommandResult.warnings`
when the card is `"banned"` or `"not_legal"`. Basic lands are exempt (they are
validated via `allowed_cards` whitelist, not the legality flag). The check runs
only when `is_validation_enabled()` returns True and `scryfall_index` is not None.

| TDD step | What to write |
|----------|---------------|
| Red | `tests/test_services.py`: `add_card` with a banned card + non-None index → `result.ok is True` but `result.warnings` contains the legality string; `add_card` with a basic land → no legality warning; `add_card` with index=None → no legality check attempted |
| Green | `src/deckslots/services.py`: after successful `add_card`, look up `commander_legal` in `validate_card` result; append to `warnings` |
| GUI wiring | `src/deckslots/gui/main_window.py`: `on_scryfall_ready` already sets `_scryfall_index`; the drop handler in `CatTile` already calls `services.can_drop` then `services.move_card` — add legality-warning passthrough from `result.warnings` to `DeckWindow.statusBar().showMessage(…)` |
| REPL wiring | `src/deckslots/cli/commands.py`: `handle_card_add` already prints `result.warnings`; verify the new warning surfaces there too (functional test addition in `tests/functional/15-validation.md`) |

**Exit**: adding Brainstorm to a Commander deck shows "Brainstorm is not legal in
Commander" in the GUI status bar and as a REPL warning. Adding Plains shows no
warning.

---

## Phase 4.5 — Documentation cleanup (US-020 / #86)

### 4.5.1 — Sync architecture docs with implemented modules

`src/deckslots/CLAUDE.md` lists 8 Phase 2 GUI modules but the filesystem has 5
additional Phase 3 modules (`deck_library.py`, `mana_panel.py`, `omnibar.py`,
`undo_stack.py`, and `__init__.py`). Update the module table with one-line
descriptions and correct phase annotations for all 13 `gui/` modules. No
production code changes.

Also check `tests/CLAUDE.md` for any test files added during Phase 3 that are
not listed.

Commit prefix: `docs:`.

### 4.5.2 — Mark roadmap phases complete

Update `docs/plans/2026-04-25-db-and-gui-roadmap.md` to mark Phase 4 complete
(add `✅` annotations and an exit note, matching the Phase 2 style).

---

## Critical file map

| Concern | New files | Modified files |
|---------|-----------|----------------|
| GUI completeness | — | `gui/app.py`, `gui/main_window.py`, `gui/board_widget.py` |
| Schema hardening | `docs/plans/2026-05-13-sqlite-migrations.md` | `storage.py` |
| Font bundling | `src/deckslots/data/fonts/DM_Sans[opsz,wght].ttf` | `gui/styles.py` |
| platformdirs | — | `config.py`, `storage.py`, `scryfall.py`, `pyproject.toml` |
| Packaging | `packaging/deckslots.spec`, `packaging/build-appimage.sh`, `packaging/deckslots.desktop`, `packaging/deckslots-256.png`, `.github/workflows/release.yml` | `pyproject.toml` |
| Performance | `tests/gui/bench_cold_open.py` | `gui/image_loader.py` |
| Accessibility | — | `gui/category_tile.py`, `gui/board_widget.py`, `gui/main_window.py` |
| Legality warnings | — | `services.py`, `gui/main_window.py`, `cli/commands.py`, `tests/functional/15-validation.md` |
| Docs | `docs/plans/2026-05-13-sqlite-migrations.md` | `src/deckslots/CLAUDE.md`, `tests/CLAUDE.md`, `docs/plans/2026-04-25-db-and-gui-roadmap.md` |
| Tests | `tests/gui/bench_cold_open.py` | `tests/gui/test_app.py`, `tests/gui/test_main_window.py`, `tests/gui/test_board_widget.py`, `tests/gui/test_category_tile.py`, `tests/gui/test_styles.py`, `tests/gui/test_image_loader.py`, `tests/test_storage_repository.py`, `tests/test_services.py`, `tests/test_config.py`, `tests/test_scryfall.py` |

---

## Ordering rationale

```
4.0 GUI completeness   ← must ship before binaries are useful
4.1 Schema hardening   ← must ship before binaries are distributed (data safety)
4.2 Packaging          ← depends on 4.0 + 4.1
4.3 Performance        ← can overlap with 4.2; independent of 4.4
4.4 Accessibility      ← independent of packaging; can overlap with 4.3
4.5 Docs               ← last; reflects the finished state
```

Steps within a section follow the numbered order above. Each step is a separate
PR with `test:` → `feat:` (→ optional `refactor:`) commits in that order.

---

## Phase 4 exit criterion

- All `uv run pytest` + `scrut test tests/functional/` suites pass on the
  `main` branch.
- `dist/deckslots --help` and `QT_QPA_PLATFORM=offscreen dist/deckslots gui`
  pass on all three platforms in CI.
- Warm-cache open of a 100-card deck with images: < 500 ms.
- All five GUI completeness gaps from the 2026-05-13 gap review are closed.
- `src/deckslots/CLAUDE.md` accurately reflects all 13 `gui/` modules.
