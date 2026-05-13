"""QApplication bootstrap for the deckslots GUI."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from deckslots.config import get_storage_backend
from deckslots.gui.main_window import DeckWindow
from deckslots.gui.styles import apply_theme
from deckslots.models import Decklist
from deckslots.scryfall import get_cache_path, load_index_from_cache
from deckslots.storage import (
    DecklistRepository,
    PlaintextRepository,
    SqliteRepository,
)


def _pick_repository() -> DecklistRepository:
    """Choose a repository based on the user's config."""
    backend = get_storage_backend()
    if backend == "sqlite":
        return SqliteRepository()
    return PlaintextRepository()


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

    if exec_loop:
        sys.exit(app.exec())
    return window
