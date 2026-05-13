"""Smoke tests for the GUI application entry point."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from deckslots.gui import app as gui_app  # noqa: E402


class TestGuiAlwaysUsesSqlite:
    def test_sqlite_used_even_when_config_says_plaintext(
        self, tmp_path, monkeypatch
    ):
        """The GUI ignores config.storage_backend and always uses SqliteRepository.

        The deck-library panel only makes sense with a multi-deck backend.
        """
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        cfg_dir = tmp_path / "deckslots"
        cfg_dir.mkdir()
        (cfg_dir / "config.json").write_text('{"storage_backend": "plaintext"}')

        called = []

        def fake_get_backend() -> str:
            called.append("get_storage_backend")
            return "plaintext"

        monkeypatch.setattr(gui_app, "get_storage_backend", fake_get_backend)

        repo = gui_app._pick_repository()
        from deckslots.storage import SqliteRepository

        assert isinstance(repo, SqliteRepository)
        assert called == []  # config not consulted


class TestLoadInitialDeck:
    def test_creates_empty_deck_when_repo_empty(self, tmp_path):
        from deckslots.storage import PlaintextRepository

        repo = PlaintextRepository(tmp_path / "decklist.bak")
        deck = gui_app._load_initial_deck(repo)
        assert deck.name  # any non-empty name
        assert "commander" in deck.categories

    def test_loads_existing_deck(self, tmp_path):
        from deckslots.models import Decklist
        from deckslots.storage import PlaintextRepository

        repo = PlaintextRepository(tmp_path / "decklist.bak")
        deck = Decklist.create("Saved Deck")
        deck.add_category("Ramp", 10)
        repo.save(deck)
        loaded = gui_app._load_initial_deck(repo)
        assert loaded.name == "Saved Deck"
        assert "ramp" in loaded.categories


class TestRunApp:
    def test_run_app_creates_window_without_blocking(
        self, qtbot, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

        win = gui_app.run_app(exec_loop=False)
        qtbot.addWidget(win)
        from deckslots.gui.main_window import DeckWindow

        assert isinstance(win, DeckWindow)
