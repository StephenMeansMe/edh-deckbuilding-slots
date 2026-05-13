"""Tests for the CardInspector preview pane."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QPixmap  # noqa: E402

from deckslots.gui.card_inspector import CardInspector  # noqa: E402


class TestPlaceholder:
    def test_initial_card_is_none(self, qtbot):
        widget = CardInspector()
        qtbot.addWidget(widget)
        assert widget.current_card is None

    def test_fixed_size_matches_design(self, qtbot):
        widget = CardInspector()
        qtbot.addWidget(widget)
        # Design spec: 180 × 280
        assert widget.minimumWidth() == 180
        assert widget.minimumHeight() == 280


class TestSetCard:
    def test_set_card_updates_current(self, qtbot):
        widget = CardInspector()
        qtbot.addWidget(widget)
        widget.set_card("Sol Ring")
        assert widget.current_card == "Sol Ring"

    def test_set_card_to_none_clears(self, qtbot):
        widget = CardInspector()
        qtbot.addWidget(widget)
        widget.set_card("Sol Ring")
        widget.set_card(None)
        assert widget.current_card is None


class TestImageDisplay:
    def test_set_image_updates_pixmap(self, qtbot):
        widget = CardInspector()
        qtbot.addWidget(widget)
        pix = QPixmap(180, 280)
        pix.fill()
        widget.set_card("Sol Ring")
        widget.set_image("Sol Ring", pix)
        assert widget.image_label.pixmap() is not None
        assert not widget.image_label.pixmap().isNull()

    def test_set_image_for_other_card_ignored(self, qtbot):
        widget = CardInspector()
        qtbot.addWidget(widget)
        widget.set_card("Sol Ring")
        pix = QPixmap(180, 280)
        pix.fill()
        widget.set_image("Some Other Card", pix)
        # Pixmap should not be set because card mismatch
        assert (
            widget.image_label.pixmap() is None
            or widget.image_label.pixmap().isNull()
        )
