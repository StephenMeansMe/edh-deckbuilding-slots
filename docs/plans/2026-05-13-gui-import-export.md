# Design: Import / Export File Dialogs (GUI)

The `Import…` and `Export…` toolbar buttons are no-ops in the current GUI. In the
REPL these operations use file-path arguments (`decklist import <path>`, `decklist export <path>`),
but a packaged desktop app has no command line for the user to type paths. The GUI
needs `QFileDialog` wrappers that feed into the same underlying format helpers.

## Goals

- Wire `Import…` to open a file picker, parse the selected file via `_parse_import_file`,
  replace the active deck, save to the repository, and refresh the board.
- Wire `Export…` to open a save picker defaulting to `<deck_name>.txt`, write the
  Moxfield-compatible format via `_format_export_file`.
- Reuse the existing format helpers in `commands.py` unchanged; no new format logic.
- Surface parse errors as a `QMessageBox.warning` rather than crashing silently.

## Non-goals

- Supporting additional formats (Moxfield JSON, MTGA `.txt`, Decked Builder `.dec`)
  at this stage. The existing plain-text format covers round-trip with Moxfield and
  Archidekt. Additional format support is a separate future story.
- Merging an imported decklist with the active one. Import always replaces, matching
  REPL semantics.

## Design

Both handlers live in `DeckWindow` in `src/deckslots/gui/main_window.py`.

### Export

```python
def _on_export(self) -> None:
    default_name = f"{self._deck.name}.txt"
    path, _ = QFileDialog.getSaveFileName(
        self, "Export Deck", default_name, "Text files (*.txt);;All files (*)"
    )
    if not path:
        return
    from deckslots.cli.commands import _format_export_file
    text = _format_export_file(self._deck)
    Path(path).write_text(text, encoding="utf-8")
    self.statusBar().showMessage(f"Exported to {Path(path).name}", 4000)
```

### Import

```python
def _on_import(self) -> None:
    path, _ = QFileDialog.getOpenFileName(
        self, "Import Deck", "", "Text files (*.txt);;All files (*)"
    )
    if not path:
        return
    from deckslots.cli.commands import _parse_import_file
    try:
        new_deck = _parse_import_file(Path(path))
    except Exception as exc:
        QMessageBox.warning(self, "Import Failed", str(exc))
        return
    self._deck = new_deck
    self._repo.save(self._deck)
    self._board.set_deck(self._deck)
    self.statusBar().showMessage(f"Imported "{new_deck.name}"", 4000)
```

### Wiring

`DeckWindow._build_toolbar()` (or the File menu actions, whichever is wired for these
buttons) connects the actions:

```python
import_action.triggered.connect(self._on_import)
export_action.triggered.connect(self._on_export)
```

## Testing strategy

- **Unit** (`tests/gui/test_main_window.py`):
  - Patch `QFileDialog.getSaveFileName` to return a tmp path; assert the file is
    written and contains the Commander section header.
  - Patch `QFileDialog.getOpenFileName` to return a fixture decklist path; assert
    `self._deck.name` changes and `repository.save` is called.
  - Patch `_parse_import_file` to raise; assert `QMessageBox.warning` is shown and
    deck is unchanged.
- **Integration**: export a deck to a temp file, mutate the file, re-import → board
  reflects the mutation.

## Critical files

- **Modified**: `src/deckslots/gui/main_window.py` (`_on_import`, `_on_export`, toolbar wiring)
- **No changes** to `src/deckslots/cli/commands.py` — format helpers are reused as-is
- **Tests**: `tests/gui/test_main_window.py`
