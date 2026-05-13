"""DeckWindow — top-level QMainWindow hosting the board, menus, and status bar."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSpinBox,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from deckslots import services
from deckslots.gui.board_widget import BoardWidget
from deckslots.gui.deck_library import DeckLibraryPanel
from deckslots.gui.image_loader import ImageLoader
from deckslots.gui.mana_panel import ManaPanel
from deckslots.gui.omnibar import Omnibar
from deckslots.gui.undo_stack import UndoStack
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
        self._mana_dock: QDockWidget | None = None
        self._mana_panel: ManaPanel | None = None
        self._undo_stack = UndoStack()

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

        # Card-search omnibar (Ctrl+K)
        self._omnibar = Omnibar(scryfall_index, deck, parent=self)
        self._omnibar.card_chosen.connect(self._on_card_chosen)
        QShortcut(QKeySequence("Ctrl+K"), self).activated.connect(self._open_omnibar)

        # Library sidebar — only for multi-deck SQLite backend
        if isinstance(repository, SqliteRepository):
            self._setup_library_dock()

        # Mana-curve panel (bottom dock)
        self._setup_mana_dock()

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

        edit_menu = menubar.addMenu("Edit")
        self._act_undo = QAction("Undo", self)
        self._act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self._act_undo.setEnabled(False)
        self._act_undo.triggered.connect(self._undo)
        self._act_redo = QAction("Redo", self)
        self._act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self._act_redo.setEnabled(False)
        self._act_redo.triggered.connect(self._redo)
        edit_menu.addAction(self._act_undo)
        edit_menu.addAction(self._act_redo)

        deck_menu = menubar.addMenu("Deck")
        deck_menu.addAction(QAction("Rename...", self))
        act_import = QAction("Import...", self)
        act_import.triggered.connect(self._on_import_deck)
        act_export = QAction("Export...", self)
        act_export.triggered.connect(self._on_export_deck)
        deck_menu.addAction(act_import)
        deck_menu.addAction(act_export)
        deck_menu.addSeparator()
        deck_menu.addAction(QAction("Enable Partner", self))
        deck_menu.addAction(QAction("Enable Background", self))
        deck_menu.addAction(QAction("Enable Companion", self))

        cat_menu = menubar.addMenu("Category")
        act_new_cat = QAction("New Category...", self)
        act_new_cat.triggered.connect(self._on_add_category)
        cat_menu.addAction(act_new_cat)

        card_menu = menubar.addMenu("Card")
        act_search = QAction("Search... (Ctrl+K)", self)
        act_search.setShortcut(QKeySequence("Ctrl+K"))
        act_search.triggered.connect(self._open_omnibar)
        card_menu.addAction(act_search)

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

    def _setup_mana_dock(self) -> None:
        """Create the mana-curve QDockWidget at the bottom."""
        self._mana_panel = ManaPanel(self._deck, index=self._scryfall_index)

        dock = QDockWidget("Mana Curve", self)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.TopDockWidgetArea
        )
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        dock.setWidget(self._mana_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self._mana_dock = dock

        toggle = dock.toggleViewAction()
        toggle.setText("Mana Curve")
        self._view_menu.addSeparator()
        self._view_menu.addAction(toggle)

    def _wire_board(self) -> None:
        """Connect board signals to window slots."""
        self.board.card_selected.connect(self._on_card_selected)
        self.board.deck_mutated.connect(self._on_deck_mutated)
        if self._mana_panel is not None:
            self.board.deck_mutated.connect(self._mana_panel.refresh)

    # ---------------------------------------------------------------
    # Deck switching
    # ---------------------------------------------------------------

    # ---------------------------------------------------------------
    # Undo / redo
    # ---------------------------------------------------------------

    def _undo(self) -> None:
        snapshot = self._undo_stack.undo(self._deck)
        if snapshot is None:
            return
        self._deck = snapshot
        self._rebuild_after_history_change()

    def _redo(self) -> None:
        snapshot = self._undo_stack.redo(self._deck)
        if snapshot is None:
            return
        self._deck = snapshot
        self._rebuild_after_history_change()

    def _rebuild_after_history_change(self) -> None:
        """Rebuild the board and persist after an undo/redo."""
        old_board = self.board
        self.board = BoardWidget(self._deck)
        self.setCentralWidget(self.board)
        self._wire_board()
        self._image_loader.image_ready.disconnect()
        self._image_loader.image_ready.connect(self.board.inspector.set_image)
        old_board.deleteLater()
        self.refresh_status_bar()
        self._act_undo.setEnabled(self._undo_stack.can_undo)
        self._act_redo.setEnabled(self._undo_stack.can_redo)
        try:
            self._repository.save(self._deck)
        except OSError:
            pass

    def _load_deck(self, deck_id: int) -> None:
        """Replace the active deck and rebuild the board."""
        try:
            new_deck = self._repository.load(deck_id)
        except KeyError:
            return
        self._current_deck_id = deck_id
        self._deck = new_deck
        self._undo_stack.reset()
        self._act_undo.setEnabled(False)
        self._act_redo.setEnabled(False)

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
        self._omnibar.update_deck(new_deck)
        if self._mana_panel is not None:
            self._mana_panel.set_deck(new_deck)
            self._mana_panel.refresh()

    # ---------------------------------------------------------------
    # Deck management actions
    # ---------------------------------------------------------------

    def _on_create_deck(self) -> None:
        taken = {s.name for s in self._repository.list()}
        name = _prompt_new_deck_name(self, taken)
        if name is None:
            return
        new_deck = Decklist.create(name)
        deck_id = self._repository.save(new_deck)
        self._load_deck(deck_id)

    def _on_export_deck(self) -> None:
        """Export the active deck to a user-chosen file."""
        from deckslots.cli.commands import _format_export_file

        default = f"{self._deck.name}.txt"
        path = _prompt_export_path(self, default)
        if path is None:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(_format_export_file(self._deck))
        except OSError as exc:
            QMessageBox.warning(self, "Export Failed", str(exc))
            return
        self.status_label.setText(f"Exported to {path}")

    def _on_import_deck(self) -> None:
        """Replace the active deck with one parsed from a user-chosen file."""
        from deckslots.cli.commands import import_deck_from_file

        path = _prompt_import_path(self)
        if path is None:
            return
        try:
            new_deck = import_deck_from_file(path)
        except (FileNotFoundError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Import Failed", str(exc))
            return
        # Save the imported deck via the repository and switch to it.
        try:
            deck_id = self._repository.save(new_deck)
        except OSError as exc:
            QMessageBox.warning(self, "Import Failed", str(exc))
            return
        if isinstance(deck_id, int) and deck_id > 0:
            self._load_deck(deck_id)
        else:
            # Plaintext repo: synthetic id is fine
            self._deck = new_deck
            self._rebuild_after_history_change()
            self._setWindowTitle()
            self._deck_name_label.setText(new_deck.name)

    def _on_add_category(self) -> None:
        """Open the Add Category dialog and create the category on accept."""
        existing = {key for key in self._deck.categories}
        result = _prompt_new_category(self, existing)
        if result is None:
            return
        name, slots = result
        outcome = services.create_category(self._deck, name, slots)
        if not outcome.ok:
            QMessageBox.warning(self, "Add Category", outcome.message)
            return
        # Rebuild the board to show the new tile; persist.
        self._rebuild_after_history_change()

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

    def _open_omnibar(self) -> None:
        self._omnibar.show()
        self._omnibar.raise_()
        self._omnibar.activateWindow()
        self._omnibar.search_input.setFocus()

    def _on_card_chosen(self, card: str, category_key: str) -> None:
        result = services.add_card(self._deck, card, category_key)
        if result.ok:
            self.board.refresh_tile(category_key)
            self._on_deck_mutated()

    # ---------------------------------------------------------------
    # Accessors
    # ---------------------------------------------------------------

    @property
    def deck(self) -> Decklist:
        return self._deck

    @property
    def repository(self) -> DecklistRepository:
        return self._repository


class _AddCategoryDialog(QDialog):
    """Modal dialog: prompt for a new user category's name and slot count.

    OK is disabled while the name is empty or duplicates an existing category
    (case-insensitive). Returns (name, slots) on accept via ``values()``.
    """

    def __init__(self, existing: set[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Category")
        self._existing = {n.lower() for n in existing}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setObjectName("CategoryName")
        self._slots_spin = QSpinBox()
        self._slots_spin.setRange(1, 99)
        self._slots_spin.setValue(8)
        form.addRow("Name:", self._name_edit)
        form.addRow("Slots:", self._slots_spin)
        layout.addLayout(form)

        self._error = QLabel()
        self._error.setStyleSheet("color: #c03010;")
        layout.addWidget(self._error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)

        self._name_edit.textChanged.connect(self._revalidate)

    def _revalidate(self, text: str) -> None:
        name = text.strip()
        if not name:
            self._error.setText("")
            self._ok_button.setEnabled(False)
            return
        if name.lower() in self._existing:
            self._error.setText(f"A category named '{name}' already exists.")
            self._ok_button.setEnabled(False)
            return
        self._error.setText("")
        self._ok_button.setEnabled(True)

    def values(self) -> tuple[str, int]:
        return self._name_edit.text().strip(), self._slots_spin.value()


def _prompt_new_category(
    parent: QWidget | None, existing: set[str]
) -> tuple[str, int] | None:
    """Show the Add Category dialog; return (name, slots) or None on cancel.

    Tests monkeypatch this module-level function to avoid actually showing
    a Qt dialog.
    """
    dlg = _AddCategoryDialog(existing, parent=parent)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    return dlg.values()


class _NewDeckDialog(QDialog):
    """Modal dialog: prompt for a new deck's name.

    OK is disabled while the name is empty or duplicates an existing deck
    in the library (case-insensitive).
    """

    def __init__(self, taken: set[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Deck")
        self._taken = {n.lower() for n in taken}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setObjectName("DeckName")
        form.addRow("Name:", self._name_edit)
        layout.addLayout(form)

        self._error = QLabel()
        self._error.setStyleSheet("color: #c03010;")
        layout.addWidget(self._error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)

        self._name_edit.textChanged.connect(self._revalidate)

    def _revalidate(self, text: str) -> None:
        name = text.strip()
        if not name:
            self._error.setText("")
            self._ok_button.setEnabled(False)
            return
        if name.lower() in self._taken:
            self._error.setText(f"A deck named '{name}' already exists.")
            self._ok_button.setEnabled(False)
            return
        self._error.setText("")
        self._ok_button.setEnabled(True)

    def value(self) -> str:
        return self._name_edit.text().strip()


def _prompt_new_deck_name(parent: QWidget | None, taken: set[str]) -> str | None:
    """Show the New Deck dialog; return the trimmed name or None on cancel.

    Tests monkeypatch this module-level function.
    """
    dlg = _NewDeckDialog(taken, parent=parent)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    return dlg.value()


def _prompt_export_path(parent: QWidget | None, default_name: str) -> str | None:
    """Open a Save As file dialog and return the chosen path, or None."""
    from PySide6.QtWidgets import QFileDialog

    path, _ = QFileDialog.getSaveFileName(
        parent, "Export Deck", default_name, "Text files (*.txt);;All files (*)"
    )
    return path or None


def _prompt_import_path(parent: QWidget | None) -> str | None:
    """Open an Open file dialog and return the chosen path, or None."""
    from PySide6.QtWidgets import QFileDialog

    path, _ = QFileDialog.getOpenFileName(
        parent, "Import Deck", "", "Text files (*.txt);;All files (*)"
    )
    return path or None
