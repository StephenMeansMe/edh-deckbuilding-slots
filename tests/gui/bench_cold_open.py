"""Phase 4.3 benchmark — measure GUI cold-open time for a 100-card deck.

Not a pytest test (runs would dominate the suite). Run manually:

    QT_QPA_PLATFORM=offscreen uv run python -m tests.gui.bench_cold_open

The script prints two timings:

  * Cold cache — no on-disk card images. Expected target: < 2 s for the
    deck-load + first-paint critical path (image fetches continue async
    in the background after this point).
  * Warm cache — all card images on disk. Expected target: < 500 ms.

Targets per US-021 / #87. Record the results in the PR description and
investigate any regression with a perf flamegraph before merging.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time


def _make_full_deck(name: str = "Bench Deck"):
    from deckslots.models import Decklist

    deck = Decklist.create(name)
    deck.add_category("Ramp", 25)
    deck.add_category("Draw", 25)
    deck.add_category("Removal", 25)
    deck.add_category("Tutors", 25)
    # 100 unique cards distributed across the four user categories
    for i in range(100):
        cat = ("Ramp", "Draw", "Removal", "Tutors")[i % 4]
        deck.add_card(f"Card {i}", cat)
    return deck


def _time_run(label: str, warm: bool) -> float:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    with tempfile.TemporaryDirectory() as tmp:
        os.environ["XDG_CONFIG_HOME"] = tmp
        os.environ["XDG_STATE_HOME"] = tmp
        os.environ["XDG_DATA_HOME"] = tmp
        os.environ["XDG_CACHE_HOME"] = tmp

        from deckslots.storage import SqliteRepository

        repo = SqliteRepository()
        repo.save(_make_full_deck())

        if warm:
            # Pre-populate the on-disk image cache (no real images needed; the
            # bench only verifies the lookup path skips the network throttle)
            from deckslots.scryfall import _image_filename, get_image_cache_dir

            cache_dir = get_image_cache_dir()
            cache_dir.mkdir(parents=True, exist_ok=True)
            # 1×1 PNG ("fake" image — the lookup is what we're timing)
            png = bytes.fromhex(
                "89504E470D0A1A0A0000000D49484452000000010000000108060000001F"
                "15C4890000000D49444154789C636400000000050001A5F645400000000049"
                "454E44AE426082"
            )
            for i in range(100):
                (cache_dir / _image_filename(f"Card {i}")).write_bytes(png)

        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        from deckslots.gui import app as gui_app

        t0 = time.perf_counter()
        win = gui_app.run_app(exec_loop=False)
        # Process events once so the first paint completes
        app.processEvents()
        elapsed = time.perf_counter() - t0
        win.close()
        print(f"  {label:18s} {elapsed * 1000:8.1f} ms")
        return elapsed


def main() -> int:
    print("Phase 4.3 cold-open benchmark — 100-card deck")
    cold = _time_run("Cold (no images):", warm=False)
    warm = _time_run("Warm (cached):", warm=True)

    print()
    cold_ok = cold < 2.0
    warm_ok = warm < 0.5
    print("  Targets: cold < 2.000 s  warm < 0.500 s")
    cold_tag = "OK" if cold_ok else "FAIL"
    warm_tag = "OK" if warm_ok else "FAIL"
    print(f"  Result:  cold {cold_tag}   warm {warm_tag}")
    return 0 if (cold_ok and warm_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
