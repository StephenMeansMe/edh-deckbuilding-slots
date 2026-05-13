#!/usr/bin/env bash
# Phase 4.2.4 — build a Linux AppImage from the PyInstaller one-dir output.
#
# Requires:
#   - PyInstaller (`uv run pyinstaller`)
#   - appimagetool on $PATH (CI downloads it; not a repo dependency)
#
# Output: dist/deckslots-linux-x86_64.AppImage

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="${REPO_ROOT}/build/appimage-stage"
APPDIR="${REPO_ROOT}/build/AppDir"
DIST="${REPO_ROOT}/dist"

rm -rf "${STAGE}" "${APPDIR}"
mkdir -p "${STAGE}" "${APPDIR}/usr/bin" "${APPDIR}/usr/share/applications" \
         "${APPDIR}/usr/share/icons/hicolor/256x256/apps" "${DIST}"

# 1. PyInstaller one-dir build into the staging area
uv run pyinstaller "${REPO_ROOT}/packaging/deckslots.spec" \
  --onedir --distpath "${STAGE}" --workpath "${REPO_ROOT}/build/pyi"

# 2. Lay out the AppDir
cp -r "${STAGE}/deckslots/." "${APPDIR}/usr/bin/"
ln -sf "usr/bin/deckslots" "${APPDIR}/AppRun"
cp "${REPO_ROOT}/packaging/deckslots.desktop" "${APPDIR}/deckslots.desktop"
cp "${REPO_ROOT}/packaging/deckslots.desktop" "${APPDIR}/usr/share/applications/deckslots.desktop"
cp "${REPO_ROOT}/packaging/deckslots.png" "${APPDIR}/deckslots.png"
cp "${REPO_ROOT}/packaging/deckslots.png" \
   "${APPDIR}/usr/share/icons/hicolor/256x256/apps/deckslots.png"

# 3. Pack the AppImage
appimagetool "${APPDIR}" "${DIST}/deckslots-linux-x86_64.AppImage"
echo "Built ${DIST}/deckslots-linux-x86_64.AppImage"
