"""QApplication bootstrap for the deckslots GUI."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import QApplication

from deckslots.config import get_storage_backend  # re-exported for test monkeypatch
from deckslots.gui.main_window import DeckWindow
from deckslots.gui.styles import apply_theme
from deckslots.models import Decklist
from deckslots.scryfall import (
    get_cache_path,
    is_cache_stale,
    load_index_from_cache,
)
from deckslots.storage import DecklistRepository, SqliteRepository

__all__ = ["run_app", "get_storage_backend"]


def _pick_repository() -> DecklistRepository:
    """Return the repository the GUI always uses (SQLite).

    The GUI's deck-library panel is multi-deck by design; the single-file
    plaintext backend has no useful workflow here. We hard-code SQLite
    regardless of ``config.json``. The REPL is unaffected.
    """
    return SqliteRepository()


def _load_initial_deck(repo: DecklistRepository) -> Decklist:
    """Load the first deck in the repository, or create a new empty deck."""
    summaries = repo.list()
    if not summaries:
        return Decklist.create("New Deck")
    try:
        return repo.load(summaries[0].id)
    except Exception:  # noqa: BLE001
        return Decklist.create("New Deck")


def _load_scryfall_index() -> dict | None:
    try:
        return load_index_from_cache(get_cache_path())
    except Exception:  # noqa: BLE001
        return None


class _WorkerSignals(QObject):
    """Signals emitted by ``_ScryfallWorker``.

    ``finished`` carries the loaded index (mapping lowercase name → card dict).
    ``failed`` carries a human-readable error string.
    """

    finished = Signal(dict)
    failed = Signal(str)


class _ScryfallWorker(QRunnable):
    """Background worker: download the Scryfall oracle_cards bulk and index it.

    Runs on a ``QThreadPool`` thread. Catches all exceptions and reports via
    ``signals.failed`` so a network error never crashes the GUI.
    """

    def __init__(self) -> None:
        super().__init__()
        self.signals = _WorkerSignals()

    def run(self) -> None:  # noqa: D401 — Qt API
        try:
            # Late import so monkeypatch in tests reaches the real symbol
            from deckslots import scryfall

            cache = scryfall.get_cache_path()
            scryfall.download_oracle_cards(cache)
            index = scryfall.load_index_from_cache(cache) or {}
            self.signals.finished.emit(index)
        except Exception as exc:  # noqa: BLE001
            self.signals.failed.emit(str(exc))


def run_app(exec_loop: bool = True) -> DeckWindow:
    """Bootstrap the GUI.

    Returns the created ``DeckWindow``. When ``exec_loop`` is True (the
    default for the ``deckslots gui`` CLI invocation) this function blocks
    on ``QApplication.exec()`` and ultimately calls ``sys.exit``; tests
    pass ``exec_loop=False`` to construct the window and return without
    entering the event loop.
    """
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        app = QApplication(sys.argv)
    apply_theme(app, "light")

    repository = _pick_repository()
    deck = _load_initial_deck(repository)
    index = _load_scryfall_index()

    window = DeckWindow(deck, repository, scryfall_index=index)
    window.resize(1280, 800)
    window.show()

    cache = get_cache_path()
    if is_cache_stale(cache):
        worker = _ScryfallWorker()
        worker.signals.finished.connect(window.on_scryfall_ready)
        worker.signals.failed.connect(window.on_scryfall_failed)
        try:
            window.status_label.setText("Updating card index…")
        except AttributeError:
            pass
        QThreadPool.globalInstance().start(worker)

    if exec_loop:
        sys.exit(app.exec())
    return window
