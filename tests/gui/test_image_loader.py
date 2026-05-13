"""Tests for the async Scryfall image loader."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QPixmap  # noqa: E402

from deckslots.gui.image_loader import ImageLoader  # noqa: E402


def _make_jpeg_bytes() -> bytes:
    """Return a tiny valid JPEG file body."""
    pix = QPixmap(2, 2)
    pix.fill()
    from PySide6.QtCore import QBuffer, QByteArray, QIODeviceBase

    buf = QBuffer()
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    pix.save(buf, "JPEG")
    return bytes(buf.data())  # type: ignore[arg-type]


class TestSynchronousCacheHit:
    def test_returns_cached_pixmap_via_signal(self, qtbot, tmp_path):
        loader = ImageLoader(cache_dir=tmp_path / "imgs")
        pix = QPixmap(2, 2)
        pix.fill()
        loader._memory_cache["Sol Ring"] = pix  # type: ignore[attr-defined]

        with qtbot.waitSignal(loader.image_ready, timeout=500) as blocker:
            loader.request("Sol Ring")
        assert blocker.args[0] == "Sol Ring"
        assert not blocker.args[1].isNull()


class TestNetworkFetch:
    def test_fetches_via_scryfall_index_and_emits(
        self, qtbot, tmp_path, monkeypatch
    ):
        # Write a real JPEG to the on-disk cache so fetch_card_image picks it up
        cache_dir = tmp_path / "imgs"
        cache_dir.mkdir()
        from deckslots.scryfall import _image_filename

        (cache_dir / _image_filename("Sol Ring")).write_bytes(_make_jpeg_bytes())

        loader = ImageLoader(cache_dir=cache_dir)
        with qtbot.waitSignal(loader.image_ready, timeout=2000) as blocker:
            loader.request("Sol Ring")
        assert blocker.args[0] == "Sol Ring"
        assert not blocker.args[1].isNull()

    def test_missing_url_does_not_emit(self, qtbot, tmp_path, monkeypatch):
        from deckslots import scryfall

        def boom(*a, **kw):  # noqa: ARG001
            raise OSError("nope")

        monkeypatch.setattr(scryfall.urllib.request, "urlopen", boom)

        loader = ImageLoader(cache_dir=tmp_path / "imgs", index=None)
        # No index, no cache — fetch_card_image returns None; no signal
        with qtbot.assertNotEmitted(loader.image_ready, wait=300):
            loader.request("Definitely Not A Card")


class TestSubsequentRequest:
    def test_second_request_hits_memory_cache(self, qtbot, tmp_path):
        cache_dir = tmp_path / "imgs"
        cache_dir.mkdir()
        from deckslots.scryfall import _image_filename

        (cache_dir / _image_filename("Sol Ring")).write_bytes(_make_jpeg_bytes())

        loader = ImageLoader(cache_dir=cache_dir)
        with qtbot.waitSignal(loader.image_ready, timeout=2000):
            loader.request("Sol Ring")
        # 2nd request: should serve from memory cache (synchronous emit)
        with qtbot.waitSignal(loader.image_ready, timeout=200) as blocker:
            loader.request("Sol Ring")
        assert blocker.args[0] == "Sol Ring"
