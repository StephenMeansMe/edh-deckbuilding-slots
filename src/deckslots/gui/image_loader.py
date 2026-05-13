"""Async Scryfall card-image loader with on-disk and in-memory caches."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QPixmap

from deckslots.scryfall import fetch_card_image

_MEMORY_CACHE_LIMIT = 200
_SCRYFALL_THROTTLE_SECONDS = 0.1


class _FetchSignals(QObject):
    """Helper QObject to carry signals out of a QRunnable worker."""

    finished = Signal(str, QPixmap)


class _FetchTask(QRunnable):
    def __init__(
        self,
        card_name: str,
        index: dict | None,
        cache_dir: Path,
        signals: _FetchSignals,
    ) -> None:
        super().__init__()
        self.card_name = card_name
        self.index = index
        self.cache_dir = cache_dir
        self.signals = signals
        self.setAutoDelete(True)

    def run(self) -> None:  # noqa: D401
        # Respect Scryfall's 50–100 ms inter-request guidance
        time.sleep(_SCRYFALL_THROTTLE_SECONDS)
        path = fetch_card_image(
            self.card_name, index=self.index, cache_dir=self.cache_dir
        )
        if path is None or not path.exists():
            return
        pix = QPixmap(str(path))
        if pix.isNull():
            return
        self.signals.finished.emit(self.card_name, pix)


class ImageLoader(QObject):
    """Fetch card images off the GUI thread; cache pixmaps in memory.

    Usage::

        loader = ImageLoader(index=scryfall_index)
        loader.image_ready.connect(inspector.set_image)
        loader.request("Sol Ring")

    Synchronous emit (next event-loop tick) for in-memory cache hits;
    otherwise schedules a worker on the global ``QThreadPool``.
    """

    image_ready = Signal(str, QPixmap)

    def __init__(
        self,
        index: dict | None = None,
        cache_dir: Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._index = index
        self._cache_dir = cache_dir
        self._memory_cache: dict[str, QPixmap] = {}
        self._signals = _FetchSignals()
        self._signals.finished.connect(self._on_fetched)
        self._inflight: set[str] = set()

    def set_index(self, index: dict | None) -> None:
        self._index = index

    def request(self, card_name: str) -> None:
        """Request the image for *card_name*; emit ``image_ready`` when available.

        Cache hit: emits synchronously (caller is on the GUI thread).
        Cache miss: schedules a fetch and emits later via queued connection.
        """
        cached = self._memory_cache.get(card_name)
        if cached is not None:
            self.image_ready.emit(card_name, cached)
            return
        if card_name in self._inflight:
            return
        self._inflight.add(card_name)
        cache_dir = self._cache_dir or Path.cwd()
        task = _FetchTask(card_name, self._index, cache_dir, self._signals)
        QThreadPool.globalInstance().start(task)

    def _on_fetched(self, card_name: str, pix: QPixmap) -> None:
        self._inflight.discard(card_name)
        if len(self._memory_cache) >= _MEMORY_CACHE_LIMIT:
            # FIFO eviction
            oldest = next(iter(self._memory_cache))
            self._memory_cache.pop(oldest, None)
        self._memory_cache[card_name] = pix
        self.image_ready.emit(card_name, pix)
