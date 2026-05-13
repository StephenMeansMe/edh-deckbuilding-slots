"""Tests for the design-token stylesheet helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from deckslots.gui.styles import (  # noqa: E402
    DARK_TOKENS,
    LIGHT_TOKENS,
    build_stylesheet,
)


class TestTokens:
    def test_light_has_expected_keys(self):
        for key in ("bg", "panel", "border", "text", "accent"):
            assert key in LIGHT_TOKENS

    def test_dark_has_same_keys_as_light(self):
        assert set(LIGHT_TOKENS) == set(DARK_TOKENS)


class TestBuildStylesheet:
    def test_returns_string(self):
        qss = build_stylesheet(LIGHT_TOKENS)
        assert isinstance(qss, str)
        assert len(qss) > 0

    def test_substitutes_bg_color(self):
        qss = build_stylesheet(LIGHT_TOKENS)
        assert LIGHT_TOKENS["bg"] in qss

    def test_dark_differs_from_light(self):
        assert build_stylesheet(LIGHT_TOKENS) != build_stylesheet(DARK_TOKENS)


class TestBundledFontLoader:
    """4.2.1 — DM Sans bundling and graceful fallback."""

    def test_apply_theme_does_not_raise_when_no_font_bundled(self, qtbot):
        """If the fonts directory has no .ttf files, apply_theme is a no-op
        for the font (existing system-ui fallback still applies)."""
        from PySide6.QtWidgets import QApplication

        from deckslots.gui import styles

        # Reset module flag so the loader runs and exercises the empty-dir path.
        styles._BUNDLED_FONT_LOADED = False

        app = QApplication.instance() or QApplication([])
        # Should not raise even when no TTFs are present.
        styles.apply_theme(app, "light")

    def test_loader_is_idempotent(self, qtbot):
        from PySide6.QtWidgets import QApplication

        from deckslots.gui import styles

        styles._BUNDLED_FONT_LOADED = False
        app = QApplication.instance() or QApplication([])
        styles.apply_theme(app, "light")
        assert styles._BUNDLED_FONT_LOADED is True
        # Second call must be a no-op (no exception, flag stays True).
        styles.apply_theme(app, "dark")
        assert styles._BUNDLED_FONT_LOADED is True
