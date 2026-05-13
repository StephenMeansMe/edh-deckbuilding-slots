# Packaging

Phase 4.2 — binary distribution for Windows, macOS, and Linux.

## Files

- `deckslots.spec` — PyInstaller spec (one-file, no console, GUI-only).
- `build-appimage.sh` — wraps PyInstaller one-dir + `appimagetool` for Linux.
- `deckslots.desktop` — Linux desktop entry shipped inside the AppImage.
- `deckslots.png` — 256×256 PNG icon shipped inside the AppImage (add before
  the first AppImage build; the script reads `packaging/deckslots.png`).

## Build locally

```bash
uv sync --extra gui
uv run pyinstaller packaging/deckslots.spec --distpath dist/
QT_QPA_PLATFORM=offscreen dist/deckslots --help        # smoke test
```

For an AppImage you additionally need `appimagetool` on `$PATH`:

```bash
bash packaging/build-appimage.sh
```

## CI

`.github/workflows/release.yml` builds all three platforms on every `v*.*.*`
tag push and attaches the artifacts to a GitHub Release.
