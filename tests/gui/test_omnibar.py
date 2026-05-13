"""Tests for Omnibar — Phase 3.2 card search overlay."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from deckslots.gui.omnibar import (  # noqa: E402
    SEARCH_MIME_TYPE,
    Omnibar,
    SearchResultModel,
)
from deckslots.models import Decklist  # noqa: E402


def _index(*names: str) -> dict:
    return {n.lower(): {"name": n, "cmc": 1, "color_identity": []} for n in names}


class TestSearchResultModel:
    def test_empty_query_returns_no_results(self, qtbot):
        model = SearchResultModel(_index("Sol Ring", "Swords to Plowshares"))
        assert model.rowCount() == 0

    def test_query_filters_by_substring(self, qtbot):
        model = SearchResultModel(
            _index("Sol Ring", "Swords to Plowshares", "Sunken Ruins")
        )
        model.set_filter("s")
        assert model.rowCount() == 3

    def test_prefix_match_comes_before_substring(self, qtbot):
        model = SearchResultModel(_index("Sol Ring", "Arcane Signet", "Signal Pest"))
        model.set_filter("si")
        # "Signal Pest" starts with "si" → should appear before "Arcane Signet"
        first = model.card_at(0)
        assert first == "Signal Pest"

    def test_results_capped_at_fifty(self, qtbot):
        names = [f"Card {i:03d}" for i in range(100)]
        model = SearchResultModel(_index(*names))
        model.set_filter("card")
        assert model.rowCount() <= 50

    def test_mime_data_uses_search_mime_type(self, qtbot):
        model = SearchResultModel(_index("Sol Ring"))
        model.set_filter("sol")
        mime = model.mimeData([0])
        assert SEARCH_MIME_TYPE in mime.formats()

    def test_mime_data_encodes_card_name(self, qtbot):
        model = SearchResultModel(_index("Sol Ring"))
        model.set_filter("sol")
        mime = model.mimeData([0])
        payload = bytes(mime.data(SEARCH_MIME_TYPE)).decode()
        assert "Sol Ring" in payload

    def test_clear_filter_empties_results(self, qtbot):
        model = SearchResultModel(_index("Sol Ring"))
        model.set_filter("sol")
        assert model.rowCount() > 0
        model.set_filter("")
        assert model.rowCount() == 0


class TestOmnibar:
    def test_search_input_exists(self, qtbot):
        deck = Decklist.create("Test")
        bar = Omnibar(_index("Sol Ring"), deck, parent=None)
        qtbot.addWidget(bar)
        assert bar.search_input is not None

    def test_typing_updates_results(self, qtbot):
        deck = Decklist.create("Test")
        bar = Omnibar(_index("Sol Ring", "Swords to Plowshares"), deck, parent=None)
        qtbot.addWidget(bar)
        bar.search_input.setText("sol")
        assert bar.result_model.rowCount() == 1

    def test_category_chips_exclude_fixed(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        bar = Omnibar(_index("Sol Ring"), deck, parent=None)
        qtbot.addWidget(bar)
        chip_names = bar.category_chip_names()
        # Commander and Basic Lands are fixed; only user categories get chips
        assert "Commander" not in chip_names
        assert "Ramp" in chip_names

    def test_card_chosen_emitted_on_accept(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        bar = Omnibar(_index("Sol Ring"), deck, parent=None)
        qtbot.addWidget(bar)
        bar.search_input.setText("sol")
        bar.set_target_category("ramp")

        with qtbot.waitSignal(bar.card_chosen, timeout=1000) as blocker:
            bar._accept()

        card_name, cat_key = blocker.args
        assert card_name == "Sol Ring"
        assert cat_key == "ramp"

    def test_no_emit_when_no_results(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        bar = Omnibar(_index("Sol Ring"), deck, parent=None)
        qtbot.addWidget(bar)
        bar.search_input.setText("")
        bar.set_target_category("ramp")
        # Should not crash
        bar._accept()

    def test_no_emit_when_no_target(self, qtbot):
        deck = Decklist.create("Test")
        bar = Omnibar(_index("Sol Ring"), deck, parent=None)
        qtbot.addWidget(bar)
        bar.search_input.setText("sol")
        # Should not crash with no target set
        bar._accept()
