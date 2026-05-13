"""CatTile widget — header + QListView for a single category, with drag/drop."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QVBoxLayout,
)

from deckslots import services
from deckslots.events import CardMoved
from deckslots.gui.card_model import CARD_MIME_TYPE, CardListModel
from deckslots.models import (
    CappedCategory,
    Category,
    Decklist,
)


def _split_mime(mime: QMimeData) -> tuple[str, str] | None:
    if not mime.hasFormat(CARD_MIME_TYPE):
        return None
    raw = bytes(mime.data(CARD_MIME_TYPE)).decode("utf-8")
    if "\t" not in raw:
        return None
    from_cat, card = raw.split("\t", 1)
    return from_cat, card


class _CardListView(QListView):
    """QListView that forwards drag events to the parent CatTile."""

    def __init__(self, tile: CatTile) -> None:
        super().__init__(tile)
        self._tile = tile
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.setUniformItemSizes(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        self._tile._handle_drag_enter(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        self._tile._handle_drag_move(event)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._tile._handle_drag_leave()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self._tile._handle_drop(event)


class CatTile(QFrame):
    """A single category tile: header (name + count badge) + card list.

    Drag/drop targets the underlying ``Decklist`` via :mod:`deckslots.services`.
    Emits :attr:`card_selected` when a card row is clicked and
    :attr:`card_moved` after a successful drop.
    """

    card_selected = Signal(str)
    card_moved = Signal(object)  # emits CardMoved event

    def __init__(self, category: Category, deck: Decklist) -> None:
        super().__init__()
        self.setObjectName("CatTile")
        self._category = category
        self._deck = deck
        self.is_fixed = category.fixed
        self.setProperty("fixedCat", "true" if self.is_fixed else "false")
        self.setAcceptDrops(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(4)

        # ---- Header row ----
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.name_label = QLabel(category.name)
        self.name_label.setObjectName("CatName")
        header.addWidget(self.name_label)

        if self.is_fixed:
            lock = QLabel("🔒")
            lock.setStyleSheet("color: #706c84;")
            header.addWidget(lock)

        header.addStretch(1)

        self.count_badge = QLabel()
        self.count_badge.setObjectName("CountBadge")
        header.addWidget(self.count_badge)
        self._refresh_count_badge()

        outer.addLayout(header)

        # ---- Body: card list ----
        self.model = CardListModel(category, parent=self)
        self.list_view = _CardListView(self)
        self.list_view.setModel(self.model)
        self.list_view.clicked.connect(self._on_clicked)
        outer.addWidget(self.list_view, stretch=1)

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------

    @property
    def category(self) -> Category:
        return self._category

    @property
    def deck(self) -> Decklist:
        return self._deck

    def refresh(self) -> None:
        """Re-read the underlying category and rebuild the view."""
        # Refetch category in case it was replaced (rename, recreate)
        key = self._category.name.lower()
        if key in self._deck.categories:
            self._category = self._deck.categories[key]
            self.name_label.setText(self._category.name)
            self.model.set_category(self._category)
        self.model.refresh()
        self._refresh_count_badge()

    def _refresh_count_badge(self) -> None:
        cat = self._category
        if isinstance(cat, CappedCategory):
            self.count_badge.setText(f"{cat.filled}/{cat.total_slots}")
            self.count_badge.setProperty("full", "true" if cat.is_full else "false")
        else:
            self.count_badge.setText(f"{cat.filled}")
            self.count_badge.setProperty("full", "false")
        # Re-polish so the property change picks up new styles
        self.count_badge.style().unpolish(self.count_badge)
        self.count_badge.style().polish(self.count_badge)

    # ---------------------------------------------------------------
    # Drop validation
    # ---------------------------------------------------------------

    def would_accept_drop(self, mime: QMimeData) -> bool:
        """Predicate used both by tests and by the live drag handlers."""
        parsed = _split_mime(mime)
        if parsed is None:
            return False
        _from, card = parsed
        return services.can_drop(self._deck, card, self._category.name.lower())

    def rejection_reason(self, card: str, from_category: str) -> str:
        """Best-effort human-readable reason that a drop would be rejected."""
        target_key = self._category.name.lower()
        target = self._deck.categories.get(target_key)
        if target is None:
            return f"Category '{self._category.name}' not found."
        if not target.user_addable:
            return f"Cards cannot be moved into '{target.name}'."
        if target.is_full:
            return f"Category '{target.name}' is full."
        if target.allowed_cards is not None and card not in target.allowed_cards:
            return f"'{card}' is not allowed in '{target.name}'."
        source_key = self._deck.find_card(card)
        if source_key == target_key:
            return f"'{card}' is already in '{target.name}'."
        if isinstance(target, CappedCategory):
            for key, other in self._deck.categories.items():
                if (
                    key != source_key
                    and isinstance(other, CappedCategory)
                    and card in other.cards
                ):
                    return f"'{card}' is already in '{other.name}'."
        return "Drop not allowed."

    # ---------------------------------------------------------------
    # Mutation
    # ---------------------------------------------------------------

    def perform_move(self, from_category: str, card: str) -> bool:
        """Execute the move via ``services.move_card`` and emit signals.

        Returns True on success.
        """
        result = services.move_card(
            self._deck, card, self._category.name.lower()
        )
        if not result.ok:
            return False
        self.refresh()
        for event in result.events:
            if isinstance(event, CardMoved):
                self.card_moved.emit(event)
        return True

    # ---------------------------------------------------------------
    # Drag handlers (forwarded by _CardListView)
    # ---------------------------------------------------------------

    def _set_drag_state(self, *, ok: bool | None) -> None:
        if ok is True:
            self.setProperty("dragOk", "true")
            self.setProperty("dragReject", "false")
        elif ok is False:
            self.setProperty("dragOk", "false")
            self.setProperty("dragReject", "true")
        else:
            self.setProperty("dragOk", "false")
            self.setProperty("dragReject", "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def _handle_drag_enter(self, event: QDragEnterEvent) -> None:
        mime = event.mimeData()
        parsed = _split_mime(mime)
        if parsed is None:
            event.ignore()
            return
        accept = self.would_accept_drop(mime)
        if accept:
            self._set_drag_state(ok=True)
            self.setToolTip("")
            event.acceptProposedAction()
        else:
            self._set_drag_state(ok=False)
            _from, card = parsed
            self.setToolTip(self.rejection_reason(card, _from))
            event.ignore()

    def _handle_drag_move(self, event: QDragMoveEvent) -> None:
        if self.would_accept_drop(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def _handle_drag_leave(self) -> None:
        self._set_drag_state(ok=None)
        self.setToolTip("")

    def _handle_drop(self, event: QDropEvent) -> None:
        parsed = _split_mime(event.mimeData())
        self._handle_drag_leave()
        if parsed is None:
            event.ignore()
            return
        from_cat, card = parsed
        if self.perform_move(from_cat, card):
            event.acceptProposedAction()
        else:
            event.ignore()

    # ---------------------------------------------------------------
    # Selection
    # ---------------------------------------------------------------

    def _on_clicked(self, index) -> None:
        card = self.model.data(index, Qt.ItemDataRole.UserRole)
        if isinstance(card, str):
            self.card_selected.emit(card)
