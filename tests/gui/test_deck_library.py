"""Tests for DeckLibraryPanel — 3.1 deck-library sidebar."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt  # noqa: E402

from deckslots.gui.deck_library import DeckLibraryPanel  # noqa: E402
from deckslots.models import Decklist  # noqa: E402
from deckslots.storage import SqliteRepository  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return SqliteRepository(tmp_path / "lib.db")


@pytest.fixture
def two_deck_repo(tmp_path):
    r = SqliteRepository(tmp_path / "lib.db")
    r.save(Decklist.create("Alpha"))
    r.save(Decklist.create("Beta"))
    return r


class TestDeckLibraryPanelDisplay:
    def test_shows_no_rows_when_repo_empty(self, qtbot, repo):
        panel = DeckLibraryPanel(repo, current_deck_id=None)
        qtbot.addWidget(panel)
        assert panel.row_count() == 0

    def test_shows_one_row_per_deck(self, qtbot, two_deck_repo):
        panel = DeckLibraryPanel(two_deck_repo, current_deck_id=None)
        qtbot.addWidget(panel)
        assert panel.row_count() == 2

    def test_row_text_shows_deck_name(self, qtbot, repo):
        repo.save(Decklist.create("Dragonstorm"))
        panel = DeckLibraryPanel(repo, current_deck_id=None)
        qtbot.addWidget(panel)
        names = panel.row_names()
        assert "Dragonstorm" in names

    def test_refresh_picks_up_new_deck(self, qtbot, repo):
        panel = DeckLibraryPanel(repo, current_deck_id=None)
        qtbot.addWidget(panel)
        assert panel.row_count() == 0
        repo.save(Decklist.create("Crabby Crab"))
        panel.refresh()
        assert panel.row_count() == 1


class TestDeckLibraryPanelSignals:
    def test_deck_selected_emitted_on_row_click(self, qtbot, two_deck_repo):
        summaries = two_deck_repo.list()
        first_id = summaries[0].id
        panel = DeckLibraryPanel(two_deck_repo, current_deck_id=None)
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.deck_selected, timeout=1000) as blocker:
            panel._click_row(0)
        assert blocker.args[0] == first_id

    def test_create_requested_emitted_on_add_button(self, qtbot, repo):
        panel = DeckLibraryPanel(repo, current_deck_id=None)
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.create_requested, timeout=1000):
            panel.add_button.click()

    def test_delete_requested_emitted_on_trash_button(self, qtbot, two_deck_repo):
        summaries = two_deck_repo.list()
        first_id = summaries[0].id
        panel = DeckLibraryPanel(two_deck_repo, current_deck_id=None)
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.delete_requested, timeout=1000) as blocker:
            panel._click_delete(0)
        assert blocker.args[0] == first_id

    def test_no_signal_when_no_rows(self, qtbot, repo):
        panel = DeckLibraryPanel(repo, current_deck_id=None)
        qtbot.addWidget(panel)
        # Should not crash when no rows
        panel._click_row(0)


class TestDeckLibraryPanelActiveState:
    def test_active_deck_id_stored(self, qtbot, two_deck_repo):
        summaries = two_deck_repo.list()
        active_id = summaries[0].id
        panel = DeckLibraryPanel(two_deck_repo, current_deck_id=active_id)
        qtbot.addWidget(panel)
        assert panel.current_deck_id == active_id

    def test_refresh_updates_active_id(self, qtbot, two_deck_repo):
        summaries = two_deck_repo.list()
        id0, id1 = summaries[0].id, summaries[1].id
        panel = DeckLibraryPanel(two_deck_repo, current_deck_id=id0)
        qtbot.addWidget(panel)
        panel.refresh(current_deck_id=id1)
        assert panel.current_deck_id == id1
