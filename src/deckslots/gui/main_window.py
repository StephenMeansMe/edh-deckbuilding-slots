"""DeckWindow — top-level QMainWindow hosting the board, menus, and status bar."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QWidget,
)

from deckslots.gui.board_widget import BoardWidget
from deckslots.gui.deck_library import DeckLibraryPanel
from deckslots.gui.image_loader import ImageLoader
from deckslots.models import Decklist
from deckslots.storage import DecklistRepository, SqliteRepository


class DeckWindow(QMainWindow):
    """Main application window: menu bar + toolbar + BoardWidget + status bar.

    Holds the active ``Decklist`` and ``DecklistRepository`` and persists
    after each mutation reported by the board.

    When the repository is a ``SqliteRepository``, a ``QDockWidget`` containing
    a ``DeckLibraryPanel`` is shown on the left so the user can switch decks
    without leaving the GUI.
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
        self._scryfall_index = scryfall_index
        self._current_deck_id: int | None = None
        self._library_dock: QDockWidget | None = None
        self._deck_library: DeckLibraryPanel | None = None

        self._setWindowTitle()
        self._setup_menus()
        self._setup_toolbar()

        self.board = BoardWidget(deck)
        self.setCentralWidget(self.board)
        self._wire_board()

        self._setup_status_bar()
        self.refresh_status_bar()

        # Async card-image loader for the inspector
        self._image_loader = ImageLoader(index=scryfall_index, parent=self)
        self._image_loader.image_ready.connect(self.board.inspector.set_image)

        # Library sidebar — only for multi-deck SQLite backend
        if isinstance(repository, SqliteRepository):
            self._setup_library_dock()

    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------

    def _setWindowTitle(self) -> None:  # noqa: N802
        self.setWindowTitle(f"deckslots — {self._deck.name}")

    def _setup_menus(self) -> None:
        menubar: QMenuBar = self.menuBar()

        file_menu = menubar.addMenu("File")
        act_new = QAction("New Deck...", self)
        act_new.triggered.connect(self._on_create_deck)
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

        self._view_menu = menubar.addMenu("View")
        self._view_menu.addAction(QAction("Light Theme", self))
        self._view_menu.addAction(QAction("Dark Theme", self))

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(QAction("About", self))

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        deck_name = QLabel(self._deck.name)
        deck_name.setObjectName("DeckName")
        toolbar.addWidget(deck_name)

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

    def _setup_library_dock(self) -> None:
        """Create and register the deck-library QDockWidget."""
        # Determine the current deck's ID in the repository
        summaries = self._repository.list()
        self._current_deck_id = next(
            (s.id for s in summaries if s.name == self._deck.name), None
        )

        self._deck_library = DeckLibraryPanel(
            self._repository,
            current_deck_id=self._current_deck_id,
        )
        self._deck_library.deck_selected.connect(self._load_deck)
        self._deck_library.create_requested.connect(self._on_create_deck)
        self._deck_library.delete_requested.connect(self._on_delete_deck)

        dock = QDockWidget("Decks", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        dock.setWidget(self._deck_library)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self._library_dock = dock

        # Add a toggle to the View menu
        toggle = dock.toggleViewAction()
        toggle.setText("Library Sidebar")
        self._view_menu.addSeparator()
        self._view_menu.addAction(toggle)

    def _wire_board(self) -> None:
        """Connect board signals to window slots."""
        self.board.card_selected.connect(self._on_card_selected)
        self.board.deck_mutated.connect(self._on_deck_mutated)

    # ---------------------------------------------------------------
    # Deck switching
    # ---------------------------------------------------------------

    def _load_deck(self, deck_id: int) -> None:
        """Replace the active deck and rebuild the board."""
        try:
            new_deck = self._repository.load(deck_id)
        except KeyError:
            return
        self._current_deck_id = deck_id
        self._deck = new_deck

        # Tear down old board and create a fresh one
        old_board = self.board
        self.board = BoardWidget(new_deck)
        self.setCentralWidget(self.board)
        self._wire_board()
        # Reconnect image loader to new inspector
        self._image_loader.image_ready.disconnect()
        self._image_loader.image_ready.connect(self.board.inspector.set_image)
        old_board.deleteLater()

        self._setWindowTitle()
        self._deck_name_label.setText(new_deck.name)
        self.refresh_status_bar()

        if self._deck_library is not None:
            self._deck_library.refresh(current_deck_id=deck_id)

    # ---------------------------------------------------------------
    # Deck management actions
    # ---------------------------------------------------------------

    def _on_create_deck(self) -> None:
        name, ok = QInputDialog.getText(self, "New Deck", "Deck name:")
        if not ok or not name.strip():
            return
        new_deck = Decklist.create(name.strip())
        deck_id = self._repository.save(new_deck)
        self._load_deck(deck_id)

    def _on_delete_deck(self, deck_id: int) -> None:
        summaries = self._repository.list()
        summary = next((s for s in summaries if s.id == deck_id), None)
        if summary is None:
            return
        btn = QMessageBox.question(
            self,
            "Delete deck",
            f"Delete '{summary.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if btn != QMessageBox.StandardButton.Yes:
            return
        self._repository.delete(deck_id)
        if self._deck_library is not None:
            self._deck_library.refresh(self._current_deck_id)

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
            self.status_label.setText(
                self.status_label.text() + " | ⚠ failed to save"
            )
        if self._deck_library is not None:
            self._deck_library.refresh(self._current_deck_id)

    # ---------------------------------------------------------------
    # Accessors
    # ---------------------------------------------------------------

    @property
    def deck(self) -> Decklist:
        return self._deck

    @property
    def repository(self) -> DecklistRepository:
        return self._repository
