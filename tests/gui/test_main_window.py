"""Tests for the DeckWindow QMainWindow."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from deckslots.gui.main_window import DeckWindow  # noqa: E402
from deckslots.models import Decklist  # noqa: E402
from deckslots.storage import PlaintextRepository  # noqa: E402


def _repo(tmp_path):
    return PlaintextRepository(tmp_path / "decklist.bak")


class TestWindowChrome:
    def test_title_includes_deck_name(self, qtbot, tmp_path):
        deck = Decklist.create("My Deck")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert "My Deck" in win.windowTitle()

    def test_status_bar_shows_slot_count(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        msg = win.status_label.text()
        # Commander has 1 slot total, 0 filled
        assert "0/1" in msg or "0 / 1" in msg

    def test_menu_bar_has_expected_menus(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        titles = [a.text() for a in win.menuBar().actions()]
        for required in ("File", "Deck", "Category", "Card", "View", "Help"):
            assert required in titles, f"Missing menu: {required}"


class TestStatusBarUpdates:
    def test_status_updates_when_card_added(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        deck.add_card("Sol Ring", "Ramp")
        win.refresh_status_bar()
        # Commander + Ramp = 1 + 10 slots; 1 filled
        assert "1/11" in win.status_label.text()

    def test_status_warns_about_uncategorized(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.remove_card("Sol Ring")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert "Uncategorized" in win.status_label.text()


class TestPersistence:
    def test_card_move_persists_via_repository(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_category("Removal", 10)
        deck.add_card("Sol Ring", "Ramp")
        repo = _repo(tmp_path)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        # Simulate a move via the board's underlying tile
        ramp_tile = win.board.masonry_tiles["ramp"]  # noqa: F841
        removal_tile = win.board.masonry_tiles["removal"]
        ok = removal_tile.perform_move("Ramp", "Sol Ring")
        assert ok is True

        # Reload from repo and check
        reloaded = repo.load(1)
        assert "Sol Ring" in reloaded.categories["removal"].cards


class TestDeckSelectedSignal:
    def test_card_selected_propagates_to_inspector(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        win.board.card_selected.emit("Sol Ring")
        assert win.board.inspector.current_card == "Sol Ring"
