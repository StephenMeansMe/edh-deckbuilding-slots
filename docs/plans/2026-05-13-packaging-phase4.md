# Design: Phase 4 — Packaging and Distribution

`deckslots` currently requires Python 3.12+ and `uv` (or `pip`) to install.
Shipping to a general user base requires distributable binaries that run without
any Python toolchain. This plan covers:

1. Font bundling (DM Sans Variable)
2. Cross-platform path handling (`platformdirs`)
3. PyInstaller one-file binaries for Windows and macOS
4. AppImage for Linux
5. GitHub Actions release CI

## Goals

- A user on Windows, macOS, or Linux can download a single file, double-click it,
  and `deckslots gui` opens.
- DM Sans Variable is bundled so the app looks identical on all platforms.
- File paths on Windows follow `%APPDATA%` / `%LOCALAPPDATA%` conventions.
- Releases are built automatically when a version tag is pushed.

## Non-goals

- A native macOS `.app` bundle with code-signing and notarization (deferred; add
  when targeting the Mac App Store).
- Auto-update within the app (deferred; GitHub Releases provides manual updates).
- Packaging the CLI-only install (no `[gui]`). The thin REPL remains installable
  via `pip install deckslots` for power users.

## 1. Font bundling

### Add the font as package data

Download `DM_Sans[opsz,wght].ttf` (SIL Open Font License) and place it at:

```
src/deckslots/data/fonts/DM_Sans[opsz,wght].ttf
```

Register it in `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/deckslots"]
# fonts/ is already included because it lives under src/deckslots/data/
```

### Load via `QFontDatabase` in `styles.py`

```python
from importlib.resources import files

def _load_dm_sans() -> None:
    font_path = files("deckslots.data.fonts").joinpath("DM_Sans[opsz,wght].ttf")
    # importlib.resources returns a Traversable; PyInstaller handles this via its
    # PKG_RESOURCES hook.
    with font_path.open("rb") as fh:
        data = fh.read()
    from PySide6.QtGui import QFontDatabase
    from PySide6.QtCore import QByteArray
    QFontDatabase.addApplicationFontFromData(QByteArray(data))
```

Call `_load_dm_sans()` at the top of `apply_theme()` before setting the stylesheet.
The `system-ui` fallback in the stylesheet remains as a safety net.

## 2. Cross-platform path handling

Replace the manual XDG env-var checks in `config.py`, `storage.py`, and
`scryfall.py` with `platformdirs`:

```toml
[project.optional-dependencies]
gui = [
    "pyside6>=6.6",
    "platformdirs>=4.0",
]
```

`platformdirs` is also useful for the CLI on macOS (returns `~/Library/…` paths);
add it as a core dependency rather than a `[gui]`-only one.

```python
# config.py — before
xdg = os.environ.get("XDG_CONFIG_HOME")
base = Path(xdg) if xdg else Path.home() / ".config"

# config.py — after
from platformdirs import user_config_dir
base = Path(user_config_dir("deckslots", appauthor=False))
```

Apply the same change in `storage.py` (`user_state_dir`, `user_data_dir`) and
`scryfall.py` (`user_cache_dir`). The XDG env-var overrides used in tests can be
replaced with `platformdirs`'s `PlatformDirs(…, multipath=False)` or by monkey-
patching the `platformdirs` functions in test fixtures.

## 3. PyInstaller spec

New file `packaging/deckslots.spec`:

```python
# packaging/deckslots.spec
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("deckslots")   # picks up data/templates/ and data/fonts/

a = Analysis(
    ["src/deckslots/cli/__init__.py"],
    pathex=[],
    datas=datas,
    hiddenimports=["deckslots.gui"],       # lazy import in cli.py
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          name="deckslots", console=False, onefile=True)
```

Build command (run in repo root with the `[gui]` extra installed):

```bash
uv run pyinstaller packaging/deckslots.spec --distpath dist/
```

`console=False` hides the terminal window on Windows (GUI-only). The REPL will not
work from this binary — that is acceptable; power users use `pip install deckslots`.

## 4. AppImage (Linux)

New script `packaging/build-appimage.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
# 1. Build the PyInstaller one-dir output
uv run pyinstaller packaging/deckslots.spec --onedir --distpath /tmp/appimage-stage/usr/bin/
# 2. Create AppDir structure
mkdir -p /tmp/AppDir/usr/{bin,share/applications,share/icons}
cp -r /tmp/appimage-stage/usr/bin/deckslots /tmp/AppDir/usr/bin/
cp packaging/deckslots.desktop /tmp/AppDir/usr/share/applications/
cp packaging/deckslots-256.png /tmp/AppDir/usr/share/icons/
# 3. Build the AppImage
appimagetool /tmp/AppDir dist/deckslots-linux-x86_64.AppImage
```

Requires `appimagetool` (downloaded by CI; not a repo dependency).

## 5. GitHub Actions release CI

New file `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags: ["v*.*.*"]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --extra gui
      - run: uv run pyinstaller packaging/deckslots.spec
      - run: bash packaging/build-appimage.sh
      - uses: actions/upload-artifact@v4
        with: { name: linux, path: dist/*.AppImage }

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --extra gui
      - run: uv run pyinstaller packaging/deckslots.spec
      - uses: actions/upload-artifact@v4
        with: { name: windows, path: dist/deckslots.exe }

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --extra gui
      - run: uv run pyinstaller packaging/deckslots.spec
      - uses: actions/upload-artifact@v4
        with: { name: macos, path: dist/deckslots }

  release:
    needs: [build-linux, build-windows, build-macos]
    runs-on: ubuntu-latest
    permissions: { contents: write }
    steps:
      - uses: actions/download-artifact@v4
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            linux/*.AppImage
            windows/deckslots.exe
            macos/deckslots
```

## Testing strategy

- **Font loading**: unit test in `tests/gui/test_styles.py` — call `apply_theme()`
  with a real `QApplication`; assert the DM Sans family is in
  `QFontDatabase.families()`.
- **platformdirs paths**: parametrize existing path tests in `tests/test_config.py`,
  `tests/test_storage_repository.py`, and `tests/test_scryfall.py` to set
  `platformdirs` env overrides instead of XDG env vars.
- **Smoke binary**: after a local PyInstaller build, run `dist/deckslots --help`
  and `dist/deckslots gui` (headless with `QT_QPA_PLATFORM=offscreen`) in CI.

## Critical files

- **New**: `packaging/deckslots.spec`, `packaging/build-appimage.sh`,
  `packaging/deckslots.desktop`, `packaging/deckslots-256.png`,
  `.github/workflows/release.yml`,
  `src/deckslots/data/fonts/DM_Sans[opsz,wght].ttf`
- **Modified**: `src/deckslots/gui/styles.py` (`_load_dm_sans`, `apply_theme`),
  `src/deckslots/config.py` (platformdirs),
  `src/deckslots/storage.py` (platformdirs),
  `src/deckslots/scryfall.py` (platformdirs),
  `pyproject.toml` (add `platformdirs>=4.0` dependency)
- **Tests**: `tests/gui/test_styles.py`, `tests/test_config.py`,
  `tests/test_storage_repository.py`, `tests/test_scryfall.py`
