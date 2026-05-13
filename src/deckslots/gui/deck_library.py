"""DeckLibraryPanel — left-side deck-list sidebar (Phase 3.1)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from deckslots.storage import DecklistRepository, DecklistSummary


class _DeckRow(QWidget):
    """Single row in the deck library list."""

    def __init__(
        self,
        summary: DecklistSummary,
        active: bool,
        on_click,
        on_delete,
    ) -> None:
        super().__init__()
        self.setObjectName("DeckRow")
        self.setProperty("active", active)
        self._summary = summary

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        name_label = QLabel(summary.name)
        name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        if active:
            name_label.setStyleSheet("font-weight: 700;")

        count_label = QLabel(f"{summary.total_filled}")
        count_label.setStyleSheet("color: #706c84; font-size: 11px;")

        trash_btn = QPushButton("🗑")
        trash_btn.setFixedSize(24, 24)
        trash_btn.setFlat(True)
        trash_btn.setToolTip("Delete deck")
        trash_btn.clicked.connect(lambda: on_delete(summary.id))

        layout.addWidget(name_label)
        layout.addWidget(count_label)
        layout.addWidget(trash_btn)

        # Clicking the row (anywhere except trash) emits deck_selected
        self._on_click = on_click
        self._summary_id = summary.id

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._on_click(self._summary_id)
        super().mousePressEvent(event)


class DeckLibraryPanel(QWidget):
    """Scrollable left panel listing all decks in the repository.

    Signals:
        deck_selected(int): deck_id of the clicked deck row.
        create_requested(): the "+" add button was clicked.
        delete_requested(int): trash icon clicked on a row (deck_id).
    """

    deck_selected = Signal(int)
    create_requested = Signal()
    delete_requested = Signal(int)

    def __init__(
        self,
        repository: DecklistRepository,
        current_deck_id: int | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("DeckLibraryPanel")
        self._repo = repository
        self._current_deck_id = current_deck_id
        self._summaries: list[DecklistSummary] = []
        self._row_widgets: list[_DeckRow] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header_bar = QWidget()
        header_bar.setObjectName("LibraryHeader")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(10, 8, 10, 8)
        title = QLabel("Decks")
        title.setStyleSheet("font-weight: 600; font-size: 13px;")
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(24, 24)
        self.add_button.setFlat(True)
        self.add_button.setToolTip("New deck")
        self.add_button.clicked.connect(self.create_requested)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.add_button)
        outer.addWidget(header_bar)

        # Scrollable row list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch(1)
        scroll.setWidget(self._list_container)
        outer.addWidget(scroll, stretch=1)

        self.refresh(current_deck_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def current_deck_id(self) -> int | None:
        return self._current_deck_id

    def refresh(self, current_deck_id: int | None = None) -> None:
        """Reload summaries from the repository and rebuild the row list."""
        if current_deck_id is not None:
            self._current_deck_id = current_deck_id
        self._summaries = self._repo.list()
        self._rebuild_rows()

    def row_count(self) -> int:
        return len(self._row_widgets)

    def row_names(self) -> list[str]:
        return [s.name for s in self._summaries]

    # ------------------------------------------------------------------
    # Test helpers (used by tests to simulate interaction without mouse events)
    # ------------------------------------------------------------------

    def _click_row(self, index: int) -> None:
        """Simulate clicking the row at *index*; emits deck_selected."""
        if index < 0 or index >= len(self._summaries):
            return
        self.deck_selected.emit(self._summaries[index].id)

    def _click_delete(self, index: int) -> None:
        """Simulate clicking the trash button on row at *index*."""
        if index < 0 or index >= len(self._summaries):
            return
        self.delete_requested.emit(self._summaries[index].id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _rebuild_rows(self) -> None:
        for row in self._row_widgets:
            row.setParent(None)
            row.deleteLater()
        self._row_widgets = []

        for summary in self._summaries:
            active = summary.id == self._current_deck_id
            row = _DeckRow(
                summary,
                active,
                on_click=lambda sid: self.deck_selected.emit(sid),
                on_delete=lambda sid: self.delete_requested.emit(sid),
            )
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)
            self._row_widgets.append(row)
