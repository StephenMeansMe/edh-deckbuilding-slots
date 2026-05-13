"""Deck board: pinned row + masonry of category tiles + Uncategorized sidebar."""

from __future__ import annotations

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from deckslots import services
from deckslots.events import CardMoved, CardRemoved
from deckslots.gui.card_inspector import CardInspector
from deckslots.gui.card_model import CARD_MIME_TYPE, CardListModel
from deckslots.gui.category_tile import CatTile, _split_mime
from deckslots.models import Decklist

COMMANDER_WIDTH = 180
INSPECTOR_WIDTH = 180
SIDEBAR_WIDTH = 220
MASONRY_COLUMNS = 3


class UncatSidebar(QFrame):
    """Right-side dashed-bordered drop target listing uncategorized cards."""

    card_selected = Signal(str)
    card_moved = Signal(object)  # emits CardMoved

    def __init__(self, deck: Decklist) -> None:
        super().__init__()
        self.setObjectName("UncatSidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setAcceptDrops(True)
        self._deck = deck

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(6)

        header = QLabel("⚠ Uncategorized")
        header.setStyleSheet("font-weight: 600; color: #d49820; font-size: 13px;")
        outer.addWidget(header)

        self.subheader = QLabel()
        self.subheader.setStyleSheet("color: #706c84; font-size: 11px;")
        outer.addWidget(self.subheader)

        # ListView backed by the live Uncategorized category (created on demand)
        self._ensure_uncat()
        self._model = CardListModel(self._uncat_category(), parent=self)
        self.list_view = QListView(self)
        self.list_view.setModel(self._model)
        self.list_view.setDragEnabled(True)
        self.list_view.clicked.connect(self._on_clicked)
        outer.addWidget(self.list_view, stretch=1)

        self.refresh()

    # ---------------------------------------------------------------
    # Underlying category management
    # ---------------------------------------------------------------

    def _ensure_uncat(self) -> None:
        if "uncategorized" not in self._deck.categories:
            # Triggers lazy creation
            from deckslots.models import UncappedCategory

            self._deck.categories["uncategorized"] = UncappedCategory(
                name="Uncategorized",
                fixed=True,
                allowed_cards=None,
                user_addable=False,
                cards=[],
            )

    def _uncat_category(self):
        return self._deck.categories["uncategorized"]

    def cards(self) -> list[str]:
        return list(self._uncat_category().cards)

    def refresh(self) -> None:
        self._ensure_uncat()
        self._model.set_category(self._uncat_category())
        count = len(self._uncat_category().cards)
        if count == 0:
            self.subheader.setText("All cards placed ✓")
        else:
            self.subheader.setText(f"{count} card(s)")

    def _on_clicked(self, index) -> None:
        card = self._model.data(index, Qt.ItemDataRole.UserRole)
        if isinstance(card, str):
            self.card_selected.emit(card)

    # ---------------------------------------------------------------
    # Drop support: drop here = remove (soft delete to Uncategorized)
    # ---------------------------------------------------------------

    def _accepts(self, mime: QMimeData) -> bool:
        parsed = _split_mime(mime)
        if parsed is None:
            return False
        _from, card = parsed
        source_key = self._deck.find_card(card)
        return source_key is not None and source_key != "uncategorized"

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if self._accepts(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        if self._accepts(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        parsed = _split_mime(event.mimeData())
        if parsed is None:
            event.ignore()
            return
        _from, card = parsed
        result = services.remove_card(self._deck, card)
        if not result.ok:
            event.ignore()
            return
        self.refresh()
        for ev in result.events:
            if isinstance(ev, CardRemoved):
                self.card_moved.emit(
                    CardMoved(
                        card=card,
                        from_category=ev.from_category,
                        to_category="Uncategorized",
                    )
                )
        event.acceptProposedAction()


class BoardWidget(QWidget):
    """Top-level deck-board widget composed of three regions.

    1. Pinned row: Commander tile · Basic Lands tile · CardInspector
    2. Masonry of user categories (3 newspaper-style columns)
    3. Uncategorized sidebar (right, dashed border)
    """

    card_selected = Signal(str)
    card_moved = Signal(object)  # CardMoved
    deck_mutated = Signal()  # any change requiring repository.save

    def __init__(self, deck: Decklist) -> None:
        super().__init__()
        self._deck = deck
        self.masonry_tiles: dict[str, CatTile] = {}
        self._column_index: dict[str, int] = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Center column (pinned row + masonry)
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(10)

        # --- Pinned row ---
        pinned = QHBoxLayout()
        pinned.setSpacing(10)
        self.commander_tile = CatTile(deck.categories["commander"], deck)
        self.commander_tile.setFixedWidth(COMMANDER_WIDTH)
        self.basic_lands_tile = CatTile(deck.categories["basic lands"], deck)
        self.inspector = CardInspector()

        pinned.addWidget(self.commander_tile)
        pinned.addWidget(self.basic_lands_tile, stretch=1)
        pinned.addWidget(self.inspector)
        center_layout.addLayout(pinned)

        # --- Masonry scroll area ---
        self._masonry_host = QWidget()
        self._masonry_layout = QHBoxLayout(self._masonry_host)
        self._masonry_layout.setContentsMargins(0, 0, 0, 0)
        self._masonry_layout.setSpacing(10)
        self._columns: list[QVBoxLayout] = []
        for _ in range(MASONRY_COLUMNS):
            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 0, 0)
            col_layout.setSpacing(10)
            col_layout.addStretch(1)
            self._columns.append(col_layout)
            self._masonry_layout.addWidget(col_widget)

        scroll = QScrollArea()
        scroll.setWidget(self._masonry_host)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        center_layout.addWidget(scroll, stretch=1)

        root.addWidget(center, stretch=1)

        # --- Right sidebar: Uncategorized ---
        self.uncat_sidebar = UncatSidebar(deck)
        root.addWidget(self.uncat_sidebar)

        # Wire pinned tiles' signals
        for tile in (self.commander_tile, self.basic_lands_tile):
            tile.card_selected.connect(self.card_selected)
            tile.card_moved.connect(self._propagate_moved)
        self.uncat_sidebar.card_selected.connect(self.card_selected)
        self.uncat_sidebar.card_moved.connect(self._propagate_moved)

        self.rebuild_masonry()

    # ---------------------------------------------------------------
    # Masonry management
    # ---------------------------------------------------------------

    def _clear_masonry(self) -> None:
        for tile in self.masonry_tiles.values():
            tile.setParent(None)
            tile.deleteLater()
        self.masonry_tiles = {}
        self._column_index = {}

    def rebuild_masonry(self) -> None:
        """Tear down and redistribute user categories across the columns."""
        self._clear_masonry()
        user_categories = [
            (k, c)
            for k, c in self._deck.categories.items()
            if not c.fixed and k not in ("uncategorized",)
        ]
        for idx, (key, cat) in enumerate(user_categories):
            tile = CatTile(cat, self._deck)
            tile.card_selected.connect(self.card_selected)
            tile.card_moved.connect(self._propagate_moved)
            self.masonry_tiles[key] = tile
            col_idx = idx % MASONRY_COLUMNS
            self._column_index[key] = col_idx
            # Insert above the stretch
            col_layout = self._columns[col_idx]
            col_layout.insertWidget(col_layout.count() - 1, tile)

    def _column_of(self, key: str) -> int:
        return self._column_index.get(key, -1)

    def refresh_tile(self, name: str) -> None:
        """Refresh a single tile (Commander / Basic Lands / user category)."""
        key = name.lower()
        if key == "commander":
            self.commander_tile.refresh()
        elif key == "basic lands":
            self.basic_lands_tile.refresh()
        elif key in self.masonry_tiles:
            self.masonry_tiles[key].refresh()

    def refresh_all_tiles(self) -> None:
        self.commander_tile.refresh()
        self.basic_lands_tile.refresh()
        for tile in self.masonry_tiles.values():
            tile.refresh()
        self.uncat_sidebar.refresh()

    # ---------------------------------------------------------------
    # Signal plumbing
    # ---------------------------------------------------------------

    def _propagate_moved(self, event) -> None:
        # Refresh source + target tiles since both are now stale
        if hasattr(event, "from_category"):
            self.refresh_tile(event.from_category)
        if hasattr(event, "to_category"):
            self.refresh_tile(event.to_category)
        self.uncat_sidebar.refresh()
        self.card_moved.emit(event)
        self.deck_mutated.emit()

    # Helper to expose the CARD_MIME_TYPE constant if needed
    _MIME = CARD_MIME_TYPE
