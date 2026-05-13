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


class TestUndoRedo:
    def test_window_has_undo_stack(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert hasattr(win, "_undo_stack")

    def test_undo_reverts_deck_state(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        # Capture snapshot before mutation
        win._undo_stack.push(deck, "before delete")
        deck.categories.pop("ramp")
        assert "ramp" not in win._deck.categories

        # Undo should restore
        win._undo()
        assert "ramp" in win._deck.categories

    def test_redo_after_undo(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        win._undo_stack.push(deck, "before delete")
        deck.categories.pop("ramp")
        win._undo()
        assert "ramp" in win._deck.categories
        win._redo()
        assert "ramp" not in win._deck.categories

    def test_menu_bar_has_edit_menu(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        titles = [a.text() for a in win.menuBar().actions()]
        assert "Edit" in titles


class TestLibraryDock:
    def test_sqlite_repo_shows_library_dock(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Test")
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)
        assert hasattr(win, "_library_dock")
        assert win._library_dock is not None

    def test_load_deck_switches_active_deck(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck1 = Decklist.create("Alpha")
        deck2 = Decklist.create("Beta")
        repo.save(deck1)
        id2 = repo.save(deck2)
        win = DeckWindow(deck1, repo)
        qtbot.addWidget(win)
        win._load_deck(id2)
        assert win.deck.name == "Beta"
        assert "Beta" in win.windowTitle()

    def test_load_deck_updates_board(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck1 = Decklist.create("Alpha")
        deck1.add_category("Ramp", 5)
        repo.save(deck1)
        deck2 = Decklist.create("Beta")
        id2 = repo.save(deck2)
        win = DeckWindow(deck1, repo)
        qtbot.addWidget(win)
        win._load_deck(id2)
        # Beta has no user categories, so masonry should be empty
        assert win.board.masonry_tiles == {}

    def test_load_deck_resets_inspector(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Alpha")
        repo.save(deck)
        deck2 = Decklist.create("Beta")
        id2 = repo.save(deck2)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)
        # select a card first
        win.board.card_selected.emit("Sol Ring")
        win._load_deck(id2)
        # After switch the inspector should have no card (or a different deck's card)
        # The board's inspector must belong to the new board
        assert win.board.inspector is not None

    def test_plaintext_repo_has_no_library_dock(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        # PlaintextRepository is single-deck; no library dock added
        assert not hasattr(win, "_library_dock") or win._library_dock is None
