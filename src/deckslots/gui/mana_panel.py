"""ManaPanel — mana-curve bar chart + color-identity strip (Phase 3.4)."""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from deckslots.models import Decklist

_COLOR_ORDER = ("W", "U", "B", "R", "G", "C")
_COLOR_HEX = {
    "W": "#f9faf4",
    "U": "#0e68ab",
    "B": "#150b00",
    "R": "#d3202a",
    "G": "#00733e",
    "C": "#8c8c8c",
}


@dataclass
class CurveData:
    by_cmc: dict[int, int] = field(default_factory=dict)
    by_color: dict[str, int] = field(default_factory=dict)


def compute_curve(deck: Decklist, index: dict) -> CurveData:
    """Aggregate CMC and color-identity counts from all cards in the deck."""
    idx = index or {}
    by_cmc: dict[int, int] = {}
    by_color: dict[str, int] = {}

    for category in deck.categories.values():
        for card in category.cards:
            entry = idx.get(card.lower())
            if entry is None:
                continue
            cmc = entry.get("cmc", 0)
            bucket = min(int(cmc), 7)
            by_cmc[bucket] = by_cmc.get(bucket, 0) + 1

            colors = entry.get("color_identity", [])
            if colors:
                for c in colors:
                    by_color[c] = by_color.get(c, 0) + 1
            else:
                by_color["C"] = by_color.get("C", 0) + 1

    return CurveData(by_cmc=by_cmc, by_color=by_color)


class _CurveWidget(QWidget):
    """Bar chart over CMC buckets 0–7 (7 = 7+), drawn with QPainter."""

    _BAR_COLOR = QColor("#7c6aad")
    _BG_COLOR = QColor("#1e1b2e")
    _LABEL_COLOR = QColor("#c4bce6")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: dict[int, int] = {}
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, by_cmc: dict[int, int]) -> None:
        self._data = by_cmc
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        painter.fillRect(0, 0, w, h, self._BG_COLOR)

        buckets = list(range(8))
        counts = [self._data.get(b, 0) for b in buckets]
        max_count = max(counts) if counts else 0

        if max_count == 0:
            painter.end()
            return

        label_height = 16
        bar_area_h = h - label_height
        bar_width = w / len(buckets)

        painter.setPen(self._LABEL_COLOR)
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        for i, (bucket, count) in enumerate(zip(buckets, counts)):
            bar_h = int((count / max_count) * (bar_area_h - 4))
            x = int(i * bar_width)
            bw = int(bar_width) - 2

            painter.fillRect(x + 1, bar_area_h - bar_h, bw, bar_h, self._BAR_COLOR)

            label = "7+" if bucket == 7 else str(bucket)
            painter.drawText(x, bar_area_h, int(bar_width), label_height,
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                             label)

        painter.end()


class _ColorWidget(QWidget):
    """Horizontal strip of color-identity proportions, drawn with QPainter."""

    _BG_COLOR = QColor("#1e1b2e")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: dict[str, int] = {}
        self.setFixedHeight(20)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, by_color: dict[str, int]) -> None:
        self._data = by_color
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        painter.fillRect(0, 0, w, h, self._BG_COLOR)

        total = sum(self._data.values())
        if total == 0:
            painter.end()
            return

        x = 0
        for color in _COLOR_ORDER:
            count = self._data.get(color, 0)
            if count == 0:
                continue
            seg_w = int((count / total) * w)
            painter.fillRect(x, 0, seg_w, h, QColor(_COLOR_HEX[color]))
            x += seg_w

        # Fill any rounding gap with the last color
        if x < w:
            last_color = next(
                (c for c in reversed(_COLOR_ORDER) if self._data.get(c, 0) > 0), "C"
            )
            painter.fillRect(x, 0, w - x, h, QColor(_COLOR_HEX[last_color]))

        painter.end()


class ManaPanel(QWidget):
    """Collapsible panel showing CMC bar chart + color-identity strip."""

    def __init__(
        self,
        deck: Decklist,
        index: dict | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._deck = deck
        self._index = index or {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self._curve_widget = _CurveWidget()
        self._color_widget = _ColorWidget()
        layout.addWidget(self._curve_widget)
        layout.addWidget(self._color_widget)

        self.refresh()

    def set_deck(self, deck: Decklist) -> None:
        self._deck = deck

    def refresh(self) -> None:
        curve = compute_curve(self._deck, self._index)
        self._curve_widget.set_data(curve.by_cmc)
        self._color_widget.set_data(curve.by_color)
