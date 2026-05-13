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
    from PySide6.QtCore import QBuffer, QIODeviceBase

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


class TestThrottleSkippedOnDiskHit:
    """4.3 — disk-cache hits must not pay the Scryfall network throttle."""

    def test_disk_hit_does_not_block_on_network_throttle(self, qtbot, tmp_path):
        """A disk-cache fetch should complete in well under the 100 ms throttle."""
        import time

        from deckslots.scryfall import _image_filename

        cache_dir = tmp_path / "imgs"
        cache_dir.mkdir()
        # Pre-populate disk cache for 20 cards
        cards = [f"Card {i}" for i in range(20)]
        for c in cards:
            (cache_dir / _image_filename(c)).write_bytes(_make_jpeg_bytes())

        loader = ImageLoader(cache_dir=cache_dir)

        received: list[str] = []
        loader.image_ready.connect(lambda name, pix: received.append(name))

        t0 = time.perf_counter()
        for c in cards:
            loader.request(c)
        # Wait for all to come through
        qtbot.waitUntil(lambda: len(received) >= len(cards), timeout=2000)
        elapsed = time.perf_counter() - t0

        # 20 cards × 100 ms throttle = 2.0 s if we ran the throttle on every
        # card; with the throttle skipped on disk hits the elapsed time should
        # be a small multiple of the underlying QPixmap-load cost — well under
        # 1 s even on a slow CI runner.
        assert elapsed < 1.0, f"Expected fast disk-hit batch, took {elapsed:.2f}s"


class TestNetworkThrottleShared:
    """4.3 — concurrent network fetches share a single rate limiter."""

    def test_two_concurrent_fetches_serialise_on_throttle(self, monkeypatch):
        """Two _network_throttle() calls on different threads are at least
        _SCRYFALL_THROTTLE_SECONDS apart."""
        import threading
        import time

        from deckslots.gui import image_loader as il

        # Reset the module-level last-fetch timer so the test starts clean.
        il._LAST_NETWORK_FETCH = 0.0

        times: list[float] = []

        def worker():
            il._network_throttle()
            times.append(time.monotonic())

        # Pre-warm: the first call returns immediately because
        # _LAST_NETWORK_FETCH is 0.
        il._network_throttle()
        base = time.monotonic()

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        sorted_offsets = sorted(t - base for t in times)
        # Three additional fetches → at least 3 × throttle of separation total.
        # Allow a small jitter band.
        assert sorted_offsets[-1] >= il._SCRYFALL_THROTTLE_SECONDS * 2.5


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
