# deckslots v0.9 — Acceptance Test Release

This release is intended for acceptance testing by human users. It is
feature-complete against the Phase 0–4 roadmap; rough edges and deferred
features are noted below.

## What's new since the GUI MVP (v0.8 / Phase 2)

### Multi-deck library (Phase 1)
- SQLite backend stores every deck you create; no more single-file saves
- `decklist list`, `decklist switch <name>`, `decklist delete <name>` REPL commands
- Legacy `decklist.bak` auto-imported to the new library on first launch
- Config opt-in (`storage_backend = "sqlite"`) — plaintext still works

### Deck Library, Search & Undo (Phase 3)
- **Deck Library sidebar** — all saved decks listed; click to switch
- **Omnibar typeahead** — start typing a card name; completions come from the
  local Scryfall oracle-cards index
- **Undo / Redo** — full event log persisted in the `events` SQLite table;
  Ctrl+Z / Ctrl+Y work across sessions
- **Mana curve panel** — colour-identity breakdown and curve chart in the
  inspector area

### GUI completeness (Phase 4)
- **New Deck** (`File › New Deck…`) and **Add Category** (`Category › New
  Category…`) dialogs with inline validation — you can now start a deck
  entirely from within the GUI
- **Import / Export** (`File › Import…` / `File › Export…`) wired to the
  native file-picker — same format as the REPL `decklist import` / `export`
- **Scryfall first-run download** runs in the background; the window opens
  immediately instead of freezing for several seconds

### Distribution & paths (Phase 4)
- `platformdirs` for cross-platform config/state/data/cache directories
  (no more hard-coded XDG paths)
- PyInstaller one-file binary (`packaging/deckslots.spec`)
- Linux AppImage build script (`packaging/build-appimage.sh`)
- GitHub Actions release workflow builds Linux/Windows/macOS binaries on
  every `v*.*.*` tag

### Performance (Phase 4)
- Image loader skips the Scryfall rate-limit throttle for images that are
  already on disk; parallel `QRunnable` workers fetch missing images
- 100-card deck cold open: **80 ms** (target < 2 s ✅); warm: **43 ms**
  (target < 500 ms ✅)

### Accessibility (Phase 4)
- **Keyboard Move Card** — `Shift+M` (`Card › Move Card…`) lets keyboard-only
  users move a selected card without touching the mouse
- Accessible names and descriptions on category tiles, the card inspector,
  and the status bar (screen-reader friendly)
- **Commander legality warnings** — if the Scryfall index is loaded and a card
  is banned or not legal in Commander, a non-blocking warning appears in the
  status bar (the card is still added — advisory only)

## Known open issues (deferred to v1.0)

- **#75 US-016 — Multi-session REPL**: switching between multiple open decklists
  within a single REPL session is not yet implemented. Each session manages one
  active deck.
- **#84 US-018 — Drag to reorder categories**: category tiles are displayed in
  insertion order and cannot be rearranged by dragging. The `position` column in
  the SQLite schema is reserved for this feature.

## Installation

```
pip install "deckslots[gui]"
```

Or download the platform binary from the assets below and run it directly
(no Python required).

> **Note:** The DM Sans font is not bundled in the PyPI wheel due to licence
> distribution requirements. The app falls back to your system sans-serif if
> DM Sans is not installed. Binary releases built via the CI workflow bundle
> the font automatically.
