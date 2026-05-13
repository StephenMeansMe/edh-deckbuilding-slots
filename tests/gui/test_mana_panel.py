"""Tests for mana-curve panel — Phase 3.4."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from deckslots.gui.mana_panel import ManaPanel, compute_curve  # noqa: E402
from deckslots.models import Decklist  # noqa: E402


def _index(*entries: tuple[str, int, list[str]]) -> dict:
    """Build a minimal scryfall index from (name, cmc, color_identity) tuples."""
    return {
        name.lower(): {"name": name, "cmc": cmc, "color_identity": colors}
        for name, cmc, colors in entries
    }


class TestComputeCurve:
    def test_single_card_populates_cmc_bucket(self):
        idx = _index(("Sol Ring", 2, []))
        deck = Decklist.create("D")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        curve = compute_curve(deck, idx)
        assert curve.by_cmc[2] == 1

    def test_cmc_seven_plus_bucketed_at_seven(self):
        idx = _index(("Blightsteel Colossus", 12, []))
        deck = Decklist.create("D")
        deck.add_category("Threats", 10)
        deck.add_card("Blightsteel Colossus", "Threats")
        curve = compute_curve(deck, idx)
        assert curve.by_cmc[7] == 1

    def test_colorless_card_counted_under_C(self):
        idx = _index(("Sol Ring", 2, []))
        deck = Decklist.create("D")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        curve = compute_curve(deck, idx)
        assert curve.by_color["C"] == 1

    def test_red_card_counted_under_R(self):
        idx = _index(("Lightning Bolt", 1, ["R"]))
        deck = Decklist.create("D")
        deck.add_category("Removal", 10)
        deck.add_card("Lightning Bolt", "Removal")
        curve = compute_curve(deck, idx)
        assert curve.by_color["R"] == 1

    def test_multicolor_card_counted_once_per_color(self):
        idx = _index(("Dimir Signet", 2, ["U", "B"]))
        deck = Decklist.create("D")
        deck.add_category("Ramp", 10)
        deck.add_card("Dimir Signet", "Ramp")
        curve = compute_curve(deck, idx)
        assert curve.by_color["U"] == 1
        assert curve.by_color["B"] == 1

    def test_multiple_cards_accumulate(self):
        idx = _index(
            ("Sol Ring", 2, []),
            ("Lightning Bolt", 1, ["R"]),
        )
        deck = Decklist.create("D")
        deck.add_category("Mix", 10)
        deck.add_card("Sol Ring", "Mix")
        deck.add_card("Lightning Bolt", "Mix")
        curve = compute_curve(deck, idx)
        assert curve.by_cmc[1] == 1
        assert curve.by_cmc[2] == 1
        assert curve.by_color["C"] == 1
        assert curve.by_color["R"] == 1

    def test_cards_missing_from_index_are_skipped(self):
        deck = Decklist.create("D")
        deck.add_category("Mix", 10)
        deck.add_card("Unknown Card", "Mix")
        curve = compute_curve(deck, {})
        assert sum(curve.by_cmc.values()) == 0

    def test_basic_lands_included_in_curve(self):
        idx = _index(("Plains", 0, ["W"]))
        deck = Decklist.create("D")
        deck.add_card("Plains", "Basic Lands")
        curve = compute_curve(deck, idx)
        assert curve.by_cmc[0] == 1
        assert curve.by_color["W"] == 1

    def test_empty_deck_produces_empty_curve(self):
        deck = Decklist.create("D")
        curve = compute_curve(deck, {})
        assert sum(curve.by_cmc.values()) == 0
        assert sum(curve.by_color.values()) == 0


class TestManaPanel:
    def test_panel_renders_without_crash(self, qtbot):
        deck = Decklist.create("D")
        panel = ManaPanel(deck, index={})
        qtbot.addWidget(panel)
        panel.refresh()

    def test_panel_accepts_empty_index(self, qtbot):
        deck = Decklist.create("D")
        panel = ManaPanel(deck, index=None)
        qtbot.addWidget(panel)
        panel.refresh()

    def test_panel_refresh_after_card_added(self, qtbot):
        idx = _index(("Sol Ring", 2, []))
        deck = Decklist.create("D")
        deck.add_category("Ramp", 10)
        panel = ManaPanel(deck, index=idx)
        qtbot.addWidget(panel)
        deck.add_card("Sol Ring", "Ramp")
        panel.refresh()

    def test_panel_updates_deck_reference(self, qtbot):
        idx = _index(("Sol Ring", 2, []))
        deck = Decklist.create("D")
        panel = ManaPanel(deck, index=idx)
        qtbot.addWidget(panel)
        deck2 = Decklist.create("D2")
        panel.set_deck(deck2)
        panel.refresh()
