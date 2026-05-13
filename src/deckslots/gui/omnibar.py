"""Omnibar — floating card-search overlay triggered by Ctrl+K (Phase 3.2)."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from deckslots.gui.card_model import SEARCH_MIME_TYPE
from deckslots.models import Decklist

_MAX_RESULTS = 50


class SearchResultModel:
    """Filtered list of card names from the Scryfall index.

    Not a QAbstractListModel — intentionally kept as a plain list container
    with a Qt-free API so it can be tested without a QApplication. The
    QListView in Omnibar uses an adapter.
    """

    def __init__(self, index: dict) -> None:
        self._index = index
        self._results: list[str] = []

    def set_filter(self, query: str) -> None:
        """Filter the index by *query* (prefix-first, then substring)."""
        if not query:
            self._results = []
            return
        q = query.lower()
        prefix = [self._index[k]["name"] for k in self._index if k.startswith(q)]
        contains = [
            self._index[k]["name"]
            for k in self._index
            if q in k and not k.startswith(q)
        ]
        self._results = (prefix + contains)[:_MAX_RESULTS]

    def rowCount(self) -> int:
        return len(self._results)

    def card_at(self, row: int) -> str | None:
        if 0 <= row < len(self._results):
            return self._results[row]
        return None

    def mimeData(self, indexes: list) -> QMimeData:
        """Return SEARCH_MIME_TYPE data for the given row indexes."""
        mime = QMimeData()
        if indexes:
            row = indexes[0].row() if hasattr(indexes[0], "row") else indexes[0]
            card = self.card_at(row)
            if card:
                mime.setData(SEARCH_MIME_TYPE, card.encode())
        return mime


class _ResultListView(QListView):
    """QListView subclass wired to SearchResultModel via a simple adapter."""

    def __init__(
        self, result_model: SearchResultModel, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._result_model = result_model
        from PySide6.QtCore import QAbstractListModel, QModelIndex

        class _Adapter(QAbstractListModel):
            def __init__(self, rm: SearchResultModel) -> None:
                super().__init__()
                self._rm = rm

            def rowCount(self, parent=QModelIndex()):  # noqa: B008
                return self._rm.rowCount()

            def data(self, index, role=Qt.ItemDataRole.DisplayRole):
                if role == Qt.ItemDataRole.DisplayRole:
                    return self._rm.card_at(index.row())
                return None

            def refresh(self):
                self.layoutChanged.emit()

        self._adapter = _Adapter(result_model)
        self.setModel(self._adapter)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setMaximumHeight(8 * 28)

    def refresh(self) -> None:
        self._adapter.refresh()


class Omnibar(QDialog):
    """Floating card-search dialog. Open with Ctrl+K, close with Esc.

    Emits ``card_chosen(card_name, category_key)`` when the user confirms
    a card addition. ``DeckWindow`` calls ``services.add_card`` in response.
    """

    card_chosen = Signal(str, str)  # card_name, category_key

    def __init__(
        self,
        scryfall_index: dict | None,
        deck: Decklist,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._index = scryfall_index or {}
        self._deck = deck
        self._target_category: str | None = None
        self._active_row: int = 0

        self.result_model = SearchResultModel(self._index)

        self._build_ui()
        self._rebuild_category_chips()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_deck(self, deck: Decklist) -> None:
        """Called after a deck switch; rebuilds category chips."""
        self._deck = deck
        self._rebuild_category_chips()

    def set_target_category(self, key: str) -> None:
        self._target_category = key.lower()

    def category_chip_names(self) -> list[str]:
        """Return the names of user (non-fixed) categories shown as chips."""
        return [
            cat.name
            for cat in self._deck.categories.values()
            if not cat.fixed
        ]

    def _accept(self) -> None:
        """Emit card_chosen if a result and target are selected."""
        if self.result_model.rowCount() == 0:
            return
        if self._target_category is None:
            return
        card = self.result_model.card_at(self._active_row)
        if card is None:
            return
        self.card_chosen.emit(card, self._target_category)
        self.search_input.clear()
        self.hide()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("OmnibarPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search cards to add… (Ctrl+K)")
        self.search_input.setObjectName("OmnibarInput")
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.installEventFilter(self)
        panel_layout.addWidget(self.search_input)

        self._result_view = _ResultListView(self.result_model)
        panel_layout.addWidget(self._result_view)

        self._chips_row = QWidget()
        self._chips_layout = QHBoxLayout(self._chips_row)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(6)
        panel_layout.addWidget(self._chips_row)

        hint = QLabel("↑↓ navigate · Enter to add · Esc to close")
        hint.setObjectName("OmnibarHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(hint)

        outer.addWidget(panel)

    def _rebuild_category_chips(self) -> None:
        for i in reversed(range(self._chips_layout.count())):
            item = self._chips_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        user_cats = [
            (key, cat)
            for key, cat in self._deck.categories.items()
            if not cat.fixed
        ]
        for key, cat in user_cats:
            btn = QPushButton(cat.name)
            btn.setCheckable(True)
            btn.setObjectName("CategoryChip")
            btn.clicked.connect(lambda checked, k=key: self._on_chip_clicked(k))
            self._chips_layout.addWidget(btn)

        if user_cats and self._target_category is None:
            self._target_category = user_cats[0][0]

    def _on_chip_clicked(self, key: str) -> None:
        self._target_category = key
        for i in range(self._chips_layout.count()):
            item = self._chips_layout.itemAt(i)
            if item and item.widget():
                btn = item.widget()
                chip_key = btn.text().lower()
                btn.setChecked(chip_key == key)

    def _on_text_changed(self, text: str) -> None:
        self.result_model.set_filter(text.lower())
        self._result_view.refresh()
        self._active_row = 0

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self.search_input and isinstance(event, QKeyEvent):
            key = event.key()
            if key == Qt.Key.Key_Down:
                self._active_row = min(
                    self._active_row + 1, self.result_model.rowCount() - 1
                )
                return True
            elif key == Qt.Key.Key_Up:
                self._active_row = max(self._active_row - 1, 0)
                return True
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._accept()
                return True
            elif key == Qt.Key.Key_Escape:
                self.hide()
                return True
        return super().eventFilter(obj, event)
