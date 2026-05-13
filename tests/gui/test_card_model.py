"""Tests for the CardListModel: QAbstractListModel wrapping Category.cards."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt  # noqa: E402

from deckslots.gui.card_model import (  # noqa: E402
    CARD_MIME_TYPE,
    CardListModel,
)
from deckslots.models import Decklist  # noqa: E402


def _ramp_deck() -> Decklist:
    deck = Decklist.create("Test")
    deck.add_category("Ramp", 10)
    return deck


class TestRowCount:
    def test_empty_category(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        model = CardListModel(deck.categories["ramp"])
        assert model.rowCount() == 0

    def test_matches_cards_length(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        deck.add_card("Sol Ring", "Ramp")
        deck.add_card("Arcane Signet", "Ramp")
        model = CardListModel(deck.categories["ramp"])
        assert model.rowCount() == 2


class TestData:
    def test_display_role_returns_card_name(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        deck.add_card("Sol Ring", "Ramp")
        model = CardListModel(deck.categories["ramp"])
        idx = model.index(0)
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == "Sol Ring"

    def test_user_role_returns_card_name(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        deck.add_card("Sol Ring", "Ramp")
        model = CardListModel(deck.categories["ramp"])
        idx = model.index(0)
        assert model.data(idx, Qt.ItemDataRole.UserRole) == "Sol Ring"

    def test_invalid_index_returns_none(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        model = CardListModel(deck.categories["ramp"])
        idx = model.index(99)
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) is None


class TestFlags:
    def test_valid_index_is_drag_enabled(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        deck.add_card("Sol Ring", "Ramp")
        model = CardListModel(deck.categories["ramp"])
        flags = model.flags(model.index(0))
        assert flags & Qt.ItemFlag.ItemIsDragEnabled
        assert flags & Qt.ItemFlag.ItemIsSelectable


class TestMimeData:
    def test_packs_card_name_and_source_category(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        deck.add_card("Sol Ring", "Ramp")
        model = CardListModel(deck.categories["ramp"])
        mime = model.mimeData([model.index(0)])
        assert mime.hasFormat(CARD_MIME_TYPE)
        raw = bytes(mime.data(CARD_MIME_TYPE)).decode("utf-8")
        # Format: "<from_category>\t<card>"
        from_cat, card = raw.split("\t", 1)
        assert from_cat == "Ramp"
        assert card == "Sol Ring"


class TestRefresh:
    def test_reflects_external_mutation(self, qtbot):  # noqa: ARG002
        deck = _ramp_deck()
        model = CardListModel(deck.categories["ramp"])
        assert model.rowCount() == 0

        deck.add_card("Sol Ring", "Ramp")
        model.refresh()
        assert model.rowCount() == 1
        assert model.data(model.index(0), Qt.ItemDataRole.DisplayRole) == "Sol Ring"
