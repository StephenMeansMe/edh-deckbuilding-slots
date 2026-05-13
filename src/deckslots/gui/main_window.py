"""DeckWindow — top-level QMainWindow hosting the board, menus, and status bar."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenuBar,
    QStatusBar,
    QToolBar,
    QWidget,
)

from deckslots.gui.board_widget import BoardWidget
from deckslots.gui.image_loader import ImageLoader
from deckslots.models import Decklist
from deckslots.storage import DecklistRepository


class DeckWindow(QMainWindow):
    """Main application window: menu bar + toolbar + BoardWidget + status bar.

    Holds the active ``Decklist`` and ``DecklistRepository`` and persists
    after each mutation reported by the board.
    """

    def __init__(
        self,
        deck: Decklist,
        repository: DecklistRepository,
        scryfall_index: dict | None = None,
    ) -> None:
        super().__init__()
        self._deck = deck
        self._repository = repository
        self._setWindowTitle()

        self._setup_menus()
        self._setup_toolbar()

        self.board = BoardWidget(deck)
        self.setCentralWidget(self.board)
        self.board.card_selected.connect(self._on_card_selected)
        self.board.deck_mutated.connect(self._on_deck_mutated)

        self._setup_status_bar()
        self.refresh_status_bar()

        # Async card-image loader for the inspector
        self._image_loader = ImageLoader(index=scryfall_index, parent=self)
        self._image_loader.image_ready.connect(self.board.inspector.set_image)

    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------

    def _setWindowTitle(self) -> None:  # noqa: N802
        self.setWindowTitle(f"deckslots — {self._deck.name}")

    def _setup_menus(self) -> None:
        menubar: QMenuBar = self.menuBar()

        file_menu = menubar.addMenu("File")
        act_new = QAction("New Deck...", self)
        act_open = QAction("Open Deck...", self)
        act_close = QAction("Close", self)
        act_quit = QAction("Quit", self)
        act_quit.triggered.connect(self.close)
        for a in (act_new, act_open, act_close):
            file_menu.addAction(a)
        file_menu.addSeparator()
        file_menu.addAction(act_quit)

        deck_menu = menubar.addMenu("Deck")
        deck_menu.addAction(QAction("Rename...", self))
        deck_menu.addAction(QAction("Import...", self))
        deck_menu.addAction(QAction("Export...", self))
        deck_menu.addSeparator()
        deck_menu.addAction(QAction("Enable Partner", self))
        deck_menu.addAction(QAction("Enable Background", self))
        deck_menu.addAction(QAction("Enable Companion", self))

        cat_menu = menubar.addMenu("Category")
        cat_menu.addAction(QAction("New Category...", self))

        card_menu = menubar.addMenu("Card")
        card_menu.addAction(QAction("Search... (Phase 3)", self))

        view_menu = menubar.addMenu("View")
        view_menu.addAction(QAction("Light Theme", self))
        view_menu.addAction(QAction("Dark Theme", self))

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(QAction("About", self))

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        deck_name = QLabel(self._deck.name)
        deck_name.setObjectName("DeckName")
        toolbar.addWidget(deck_name)

        # Stub of sub-line — will be filled by deck.commanders / identity later
        sub = QLabel("Commander • EDH")
        sub.setObjectName("DeckSub")
        toolbar.addWidget(sub)

        sep = QWidget()
        sep.setFixedWidth(12)
        toolbar.addWidget(sep)

        self._deck_name_label = deck_name

    def _setup_status_bar(self) -> None:
        bar: QStatusBar = self.statusBar()
        bar.setSizeGripEnabled(False)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        bar.addPermanentWidget(self.status_label, 1)

    # ---------------------------------------------------------------
    # Refresh / event handlers
    # ---------------------------------------------------------------

    def refresh_status_bar(self) -> None:
        deck = self._deck
        total = deck.total_slots
        filled = deck.total_filled
        parts = [f"Slots: {filled}/{total}"]
        uncat = deck.categories.get("uncategorized")
        if uncat is not None and len(uncat.cards) > 0:
            parts.append(f"⚠ Uncategorized: {len(uncat.cards)}")
        elif filled > 0 and not deck.commander_overcrowded:
            parts.append("✓ Healthy")
        if deck.commander_overcrowded:
            parts.append("⚠ Commander overcrowded")
        if deck.companion_slot_empty:
            parts.append("⚠ Companion slot empty")
        self.status_label.setText(" | ".join(parts))

    def _on_card_selected(self, card_name: str) -> None:
        self.board.inspector.set_card(card_name)
        self._image_loader.request(card_name)

    def _on_deck_mutated(self) -> None:
        self.refresh_status_bar()
        try:
            self._repository.save(self._deck)
        except OSError:
            # Persistence error shouldn't crash the GUI; surface in status bar.
            self.status_label.setText(
                self.status_label.text() + " | ⚠ failed to save"
            )

    # ---------------------------------------------------------------
    # Accessors
    # ---------------------------------------------------------------

    @property
    def deck(self) -> Decklist:
        return self._deck

    @property
    def repository(self) -> DecklistRepository:
        return self._repository
