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


class TestScryfallFirstRun:
    """4.0.5 — Non-blocking background Scryfall index download."""

    def test_worker_emits_finished_on_success(self, qtbot, monkeypatch, tmp_path):
        from deckslots.gui.app import _ScryfallWorker

        def fake_download(dest):
            dest.write_text(
                '[{"name":"Sol Ring","legalities":{"commander":"legal"}}]'
            )

        cache = tmp_path / "oracle_cards.json"
        monkeypatch.setattr("deckslots.scryfall.get_cache_path", lambda: cache)
        monkeypatch.setattr("deckslots.scryfall.download_oracle_cards", fake_download)

        worker = _ScryfallWorker()
        results: list[dict] = []
        worker.signals.finished.connect(lambda idx: results.append(idx))
        worker.run()
        assert results, "worker should emit finished"
        assert "sol ring" in results[0]

    def test_worker_emits_failed_on_oserror(self, qtbot, monkeypatch, tmp_path):
        from deckslots.gui.app import _ScryfallWorker

        def boom(dest):
            raise OSError("network down")

        cache = tmp_path / "oracle_cards.json"
        monkeypatch.setattr("deckslots.scryfall.get_cache_path", lambda: cache)
        monkeypatch.setattr("deckslots.scryfall.download_oracle_cards", boom)

        worker = _ScryfallWorker()
        errors: list[str] = []
        worker.signals.failed.connect(lambda msg: errors.append(msg))
        worker.run()
        assert errors
        assert "network down" in errors[0]

    def test_run_app_schedules_worker_when_cache_stale(
        self, qtbot, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

        scheduled: list[object] = []

        class FakePool:
            def start(self, runnable):
                scheduled.append(runnable)

            @staticmethod
            def globalInstance():  # noqa: N802
                return FakePool()

        import deckslots.gui.app as mod

        monkeypatch.setattr(mod, "is_cache_stale", lambda path: True)
        monkeypatch.setattr(mod, "QThreadPool", FakePool)

        win = gui_app.run_app(exec_loop=False)
        qtbot.addWidget(win)
        assert scheduled, "expected a _ScryfallWorker to be queued"

    def test_run_app_uses_cached_index_when_fresh(self, qtbot, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

        import deckslots.gui.app as mod

        monkeypatch.setattr(mod, "is_cache_stale", lambda path: False)

        scheduled: list[object] = []

        class FakePool:
            def start(self, runnable):
                scheduled.append(runnable)

            @staticmethod
            def globalInstance():  # noqa: N802
                return FakePool()

        monkeypatch.setattr(mod, "QThreadPool", FakePool)

        win = gui_app.run_app(exec_loop=False)
        qtbot.addWidget(win)
        assert not scheduled, "no worker should be queued when the cache is fresh"
