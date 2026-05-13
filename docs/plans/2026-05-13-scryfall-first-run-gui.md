# Design: Scryfall First-Run Download Flow (GUI)

The REPL prompts users once at startup when the oracle card cache is absent or
stale (> 7 days). The GUI has no equivalent flow. A user who installs the `[gui]`
extra and launches `deckslots gui` for the first time gets:

- No card-name validation (omnibar search returns nothing).
- No Scryfall card images.
- No indication anything is wrong.

This plan introduces a non-blocking background download triggered at GUI startup,
with status bar feedback.

## Goals

- On GUI launch, check whether the oracle card cache is absent or stale.
- If stale: start a background `QRunnable` worker that downloads the bulk data
  without blocking the main thread or delaying deck load.
- Show a status bar message while the download is in progress and on completion
  (or failure).
- Pass the loaded index to `DeckWindow` and `ImageLoader` once the download
  completes so omnibar search and card images work.

## Non-goals

- Blocking the app on the download. The deck loads and is usable immediately;
  card search improves once the index is ready.
- A progress bar with byte counts. A spinner / text message in the status bar is
  sufficient.
- Forcing a re-download if the user is offline. The worker catches network errors
  and shows a non-fatal status message.

## Design

### New class: `_ScryfallWorker` in `src/deckslots/gui/app.py`

```python
from PySide6.QtCore import QObject, QRunnable, Signal

class _WorkerSignals(QObject):
    finished = Signal(dict)   # emits the loaded index on success
    failed = Signal(str)      # emits an error message on failure

class _ScryfallWorker(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = _WorkerSignals()

    def run(self) -> None:
        try:
            from deckslots import scryfall
            cache = scryfall.get_cache_path()
            scryfall.download_oracle_cards(cache)
            index = scryfall.load_index_from_cache(cache) or {}
            self.signals.finished.emit(index)
        except Exception as exc:
            self.signals.failed.emit(str(exc))
```

### Wiring in `run_app()`

```python
def run_app(exec_loop: bool = True) -> None:
    ...
    window = DeckWindow(deck, repo)
    window.show()

    # Non-blocking Scryfall refresh
    from deckslots import scryfall
    cache = scryfall.get_cache_path()
    if scryfall.is_cache_stale(cache):
        worker = _ScryfallWorker()
        worker.signals.finished.connect(window.on_scryfall_ready)
        worker.signals.failed.connect(window.on_scryfall_failed)
        window.statusBar().showMessage("Updating card index…")
        QThreadPool.globalInstance().start(worker)
    else:
        index = scryfall.load_index_from_cache(cache) or {}
        if index:
            window.on_scryfall_ready(index)
    ...
```

### New slots in `DeckWindow`

```python
def on_scryfall_ready(self, index: dict) -> None:
    self._scryfall_index = index
    self._board.set_scryfall_index(index)   # forwards to ImageLoader + Omnibar
    self.statusBar().showMessage("Card index ready", 4000)

def on_scryfall_failed(self, message: str) -> None:
    self.statusBar().showMessage("Card index unavailable (offline?)", 6000)
```

`BoardWidget.set_scryfall_index(index)` passes the index to `ImageLoader` and
`Omnibar` so they can begin operating. Both already accept `None` gracefully —
images show the placeholder, omnibar shows no results — so no behaviour changes
for the zero-index case.

## Testing strategy

- **Unit** (`tests/gui/test_app.py`):
  - Patch `scryfall.is_cache_stale` → True; assert `_ScryfallWorker` is submitted
    to `QThreadPool` and status bar shows "Updating card index…".
  - Patch `is_cache_stale` → False with a non-empty index; assert
    `window.on_scryfall_ready` is called synchronously with the index.
- **Unit** (`tests/gui/test_main_window.py`):
  - `on_scryfall_ready(index)` → `_scryfall_index` is set and status bar message
    matches.
  - `on_scryfall_failed("timeout")` → status bar shows the unavailable message.
- **Worker unit** (`tests/gui/test_app.py`):
  - Patch `scryfall.download_oracle_cards` to succeed; assert `signals.finished`
    emits a non-empty dict.
  - Patch `download_oracle_cards` to raise `OSError`; assert `signals.failed`
    emits a non-empty string.

## Critical files

- **Modified**: `src/deckslots/gui/app.py` (new `_ScryfallWorker`, launch logic)
- **Modified**: `src/deckslots/gui/main_window.py` (new `on_scryfall_ready`,
  `on_scryfall_failed` slots; `_scryfall_index` field)
- **Modified**: `src/deckslots/gui/board_widget.py` (`set_scryfall_index` method
  forwarding to `ImageLoader` and `Omnibar`)
- **Tests**: `tests/gui/test_app.py`, `tests/gui/test_main_window.py`
