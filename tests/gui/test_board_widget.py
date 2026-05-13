"""Tests for the BoardWidget — pinned row + masonry + Uncategorized sidebar."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from deckslots.gui.board_widget import BoardWidget  # noqa: E402
from deckslots.models import Decklist  # noqa: E402


class TestPinnedRow:
    def test_has_commander_tile(self, qtbot):
        deck = Decklist.create("Test")
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        assert board.commander_tile is not None
        assert board.commander_tile.category.name == "Commander"

    def test_has_basic_lands_tile(self, qtbot):
        deck = Decklist.create("Test")
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        assert board.basic_lands_tile is not None
        assert board.basic_lands_tile.category.name == "Basic Lands"

    def test_has_card_inspector(self, qtbot):
        deck = Decklist.create("Test")
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        assert board.inspector is not None


class TestMasonry:
    def test_empty_when_no_user_categories(self, qtbot):
        deck = Decklist.create("Test")
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        assert board.masonry_tiles == {}

    def test_one_user_category(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        assert "ramp" in board.masonry_tiles

    def test_rebuild_masonry_after_new_category(self, qtbot):
        deck = Decklist.create("Test")
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        deck.add_category("Removal", 8)
        board.rebuild_masonry()
        assert "removal" in board.masonry_tiles

    def test_user_categories_distributed_round_robin(self, qtbot):
        deck = Decklist.create("Test")
        for name in ["Ramp", "Removal", "Card Advantage", "Threats"]:
            deck.add_category(name, 8)
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        # 4 categories across 3 columns: cols 0,1,2 then col 0
        cols = [
            [k for k, c in board.masonry_tiles.items() if board._column_of(k) == i]
            for i in range(3)
        ]
        # Each column should have at least one tile
        assert all(len(c) >= 1 for c in cols)
        # Total tiles preserved
        assert sum(len(c) for c in cols) == 4


class TestUncategorizedSidebar:
    def test_sidebar_exists(self, qtbot):
        deck = Decklist.create("Test")
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        assert board.uncat_sidebar is not None

    def test_sidebar_shows_uncategorized_cards(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.remove_card("Sol Ring")  # → Uncategorized
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        assert "Sol Ring" in board.uncat_sidebar.cards()


class TestRefreshTile:
    def test_refresh_tile_picks_up_new_card(self, qtbot):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        board = BoardWidget(deck)
        qtbot.addWidget(board)
        deck.add_card("Sol Ring", "Ramp")
        board.refresh_tile("Ramp")
        assert "Sol Ring" in board.masonry_tiles["ramp"].category.cards
