"""QAbstractListModel wrapping a Category's cards for QListView."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    QAbstractListModel,
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
)

from deckslots.models import Category

CARD_MIME_TYPE = "application/x-deckslots-card"
# Sentinel MIME type for cards dragged from the Omnibar search results.
# CatTile.dropEvent branches on this to call add_card instead of move_card.
SEARCH_MIME_TYPE = "application/x-deckslots-search-card"


class CardListModel(QAbstractListModel):
    """Read-only list model exposing ``category.cards`` to a QListView.

    Mutations to the underlying category go through ``services.*`` and the
    caller invokes :meth:`refresh` to rebuild the model. Drag MIME data
    carries the source category name so drop handlers can validate.
    """

    def __init__(self, category: Category, parent=None) -> None:
        super().__init__(parent)
        self._category = category

    @property
    def category(self) -> Category:
        return self._category

    def set_category(self, category: Category) -> None:
        self.beginResetModel()
        self._category = category
        self.endResetModel()

    def refresh(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._category.cards)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or index.row() >= len(self._category.cards):
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.UserRole):
            return self._category.cards[index.row()]
        return None

    def flags(
        self, index: QModelIndex | QPersistentModelIndex
    ) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
        )

    def mimeTypes(self) -> list[str]:
        return [CARD_MIME_TYPE]

    def mimeData(self, indexes) -> QMimeData:
        mime = QMimeData()
        for idx in indexes:
            if not idx.isValid():
                continue
            card = self._category.cards[idx.row()]
            payload = f"{self._category.name}\t{card}".encode()
            mime.setData(CARD_MIME_TYPE, payload)
            break  # single-selection drag
        return mime
