"""Card preview pane — placeholder card face plus async Scryfall image."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QStackedWidget, QVBoxLayout, QWidget

CARD_W = 180
CARD_H = 280


class _PlaceholderCard(QWidget):
    """A hand-drawn-feeling placeholder card face when no image is available."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(CARD_W, CARD_H)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.title = QLabel("Click any card to preview")
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-weight: 600; font-size: 12px;")

        art_area = QFrame()
        art_area.setStyleSheet(
            "background: #f0ede7; border: 1px dashed #c0bbb0; border-radius: 4px;"
        )
        art_area.setMinimumHeight(120)

        type_line = QLabel("— type line —")
        type_line.setStyleSheet("color: #706c84; font-size: 11px;")
        type_line.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rules = QFrame()
        rules.setStyleSheet(
            "background: #f7f5f1; border: 1px dashed #c0bbb0; border-radius: 4px;"
        )
        rules.setMinimumHeight(60)

        layout.addWidget(self.title)
        layout.addWidget(art_area, stretch=2)
        layout.addWidget(type_line)
        layout.addWidget(rules, stretch=1)

    def set_title(self, text: str) -> None:
        self.title.setText(text)


class CardInspector(QFrame):
    """Fixed-size preview pane: shows placeholder card face or Scryfall image."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CardInspector")
        self.setMinimumSize(CARD_W, CARD_H)
        self.setMaximumWidth(CARD_W)

        self.current_card: str | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(0)

        self._stack = QStackedWidget()
        outer.addWidget(self._stack)

        self._placeholder = _PlaceholderCard()
        self._stack.addWidget(self._placeholder)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self._stack.addWidget(self.image_label)

        self._stack.setCurrentWidget(self._placeholder)

    def set_card(self, name: str | None) -> None:
        """Update the currently displayed card. Clears any prior image."""
        self.current_card = name
        self.image_label.clear()
        if name is None:
            self._placeholder.set_title("Click any card to preview")
        else:
            self._placeholder.set_title(name)
        self._stack.setCurrentWidget(self._placeholder)

    def set_image(self, card_name: str, pixmap: QPixmap) -> None:
        """Install *pixmap* for *card_name*, but only if it still matches.

        Async image loads may complete after the user has clicked a different
        card; the name check guards against showing the wrong image.
        """
        if card_name != self.current_card or pixmap.isNull():
            return
        scaled = pixmap.scaled(
            CARD_W,
            CARD_H,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self._stack.setCurrentWidget(self.image_label)
