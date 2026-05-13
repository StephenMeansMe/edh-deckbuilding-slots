"""Tests for the CatTile widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QMimeData  # noqa: E402

from deckslots.gui.card_model import CARD_MIME_TYPE  # noqa: E402
from deckslots.gui.category_tile import CatTile  # noqa: E402
from deckslots.models import Decklist  # noqa: E402


def _deck_with_ramp() -> Decklist:
    deck = Decklist.create("Test")
    deck.add_category("Ramp", 10)
    return deck


class TestHeader:
    def test_shows_filled_over_total(self, qtbot):
        deck = _deck_with_ramp()
        deck.add_card("Sol Ring", "Ramp")
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)
        assert "1/10" in tile.count_badge.text()

    def test_shows_uncapped_filled_count(self, qtbot):
        deck = Decklist.create("Test")
        # Basic Lands is uncapped
        tile = CatTile(deck.categories["basic lands"], deck)
        qtbot.addWidget(tile)
        assert "0" in tile.count_badge.text()

    def test_fixed_category_has_lock_marker(self, qtbot):
        deck = Decklist.create("Test")
        tile = CatTile(deck.categories["commander"], deck)
        qtbot.addWidget(tile)
        assert tile.is_fixed
        assert tile.property("fixedCat") == "true"

    def test_user_category_is_not_fixed(self, qtbot):
        deck = _deck_with_ramp()
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)
        assert not tile.is_fixed


class TestDropValidation:
    def _mime_for(self, from_cat: str, card: str) -> QMimeData:
        mime = QMimeData()
        mime.setData(CARD_MIME_TYPE, f"{from_cat}\t{card}".encode())
        return mime

    def test_accepts_legal_drop_from_uncategorized(self, qtbot):
        deck = _deck_with_ramp()
        # Put a non-basic card in Uncategorized
        deck.add_card("Sol Ring", "Ramp")
        deck.remove_card("Sol Ring")  # → Uncategorized
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)
        mime = self._mime_for("Uncategorized", "Sol Ring")
        assert tile.would_accept_drop(mime) is True

    def test_rejects_drop_when_full(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 1)
        deck.add_card("Sol Ring", "Ramp")
        deck.add_card("Arcane Signet", "Ramp")  # Not actually — full
        # Force full by raising to 1 and adding 1
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)
        mime = self._mime_for("Uncategorized", "Mind Stone")
        assert tile.would_accept_drop(mime) is False

    def test_rejects_drop_from_same_category(self, qtbot):
        deck = _deck_with_ramp()
        deck.add_card("Sol Ring", "Ramp")
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)
        mime = self._mime_for("Ramp", "Sol Ring")
        assert tile.would_accept_drop(mime) is False

    def test_rejects_unknown_mime(self, qtbot):
        deck = _deck_with_ramp()
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)
        mime = QMimeData()
        mime.setText("not a card")
        assert tile.would_accept_drop(mime) is False


class TestRejectionReason:
    def test_full_category_reason(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 1)
        deck.add_card("Sol Ring", "Ramp")
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)
        reason = tile.rejection_reason("Mind Stone", "Uncategorized")
        assert "full" in reason.lower()

    def test_basic_lands_only_reason(self, qtbot):
        deck = Decklist.create("Test")
        tile = CatTile(deck.categories["basic lands"], deck)
        qtbot.addWidget(tile)
        reason = tile.rejection_reason("Sol Ring", "Uncategorized")
        assert "allowed" in reason.lower() or "basic" in reason.lower()


class TestPerformMove:
    def test_perform_move_updates_deck_and_emits_event(self, qtbot):
        deck = _deck_with_ramp()
        deck.add_card("Sol Ring", "Ramp")
        deck.remove_card("Sol Ring")  # → Uncategorized
        tile = CatTile(deck.categories["ramp"], deck)
        qtbot.addWidget(tile)

        captured = []
        tile.card_moved.connect(lambda evt: captured.append(evt))
        ok = tile.perform_move("Uncategorized", "Sol Ring")
        assert ok is True
        assert "Sol Ring" in deck.categories["ramp"].cards
        assert len(captured) == 1
        assert captured[0].card == "Sol Ring"
        assert captured[0].to_category == "Ramp"
