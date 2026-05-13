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
