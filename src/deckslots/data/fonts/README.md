# Bundled fonts

Drop the **DM Sans Variable** TTF (`DMSans[opsz,wght].ttf`, SIL Open Font
License) into this directory before a release build. `gui.styles._load_bundled_dm_sans()`
walks this folder at startup and registers every `.ttf` it finds via
`QFontDatabase.addApplicationFontFromData`.

If no font is present the app falls back to the system `DM Sans` install, or
`system-ui` if that's also absent. Both work; bundling the font is required
only for binary distributions (PyInstaller / AppImage) where the user's
system fonts cannot be relied on.

## Source

Download the variable-axis TTF from the Google Fonts upstream:

- https://github.com/googlefonts/dm-fonts

The file is excluded from the repo (and gitignored) because of its size and
because storing it duplicates an upstream-versioned asset; CI fetches it at
release-build time.
