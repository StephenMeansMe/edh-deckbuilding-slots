# Design: "Add Category" Dialog (GUI)

The `+ Category` button in the toolbar is currently a no-op. Without it, users
cannot create new categories from the GUI at all — they would need to use the REPL
first and then open the GUI. This makes the GUI useless as a standalone deckbuilding
tool.

## Goals

- Wire the `+ Category` toolbar action to a modal dialog.
- Validate name (non-empty, unique) and slot count (1–99) before enabling OK.
- Route the creation through `services.create_category()` so all domain invariants
  are enforced identically to the REPL.
- Emit `deck_mutated` so the board refreshes and the new tile appears.

## Non-goals

- Inline-add (editing directly in the masonry grid). A modal is simpler and
  consistent with the rename flow.
- Preset templates from the dialog. Template application is a separate `Deck` menu
  item.

## Design

### New class: `_AddCategoryDialog` in `src/deckslots/gui/main_window.py`

A `QDialog` subclass with two fields:

| Field | Widget | Constraints |
|-------|--------|-------------|
| Category name | `QLineEdit` | Required; trimmed; must not match an existing category name (case-insensitive) |
| Number of slots | `QSpinBox` | Range 1–99; default 8 |

OK button is disabled until the name field is non-empty and valid. Duplicate-name
check fires on every `textChanged` signal and shows an inline red error label.

```python
class _AddCategoryDialog(QDialog):
    def __init__(self, existing_names: set[str], parent=None) -> None: ...
    # Returns (name, slots) on accept; caller reads .result()
    @property
    def category_name(self) -> str: ...
    @property
    def slot_count(self) -> int: ...
```

### Wiring in `src/deckslots/gui/main_window.py`

`DeckWindow` already builds the toolbar. Find the `+ Category` action and connect it:

```python
# In DeckWindow._build_toolbar() or __init__:
add_cat_action.triggered.connect(self._on_add_category)

def _on_add_category(self) -> None:
    existing = {name.lower() for name in self._deck.categories}
    dlg = _AddCategoryDialog(existing, parent=self)
    if dlg.exec() != QDialog.Accepted:
        return
    result = services.create_category(self._deck, dlg.category_name, dlg.slot_count)
    if result.ok:
        self._board.refresh(result.events)
        self._repo.save(self._deck)
    else:
        QMessageBox.warning(self, "Add Category", result.message)
```

`services.create_category` already validates name length, uniqueness, and slot range
(1–99) and returns a `CommandResult`. The dialog pre-validates for responsiveness, but
the service is the authoritative gate.

## Testing strategy

- **Unit** (`tests/gui/test_main_window.py`):
  - Trigger `_on_add_category` with a mock dialog that accepts → assert
    `services.create_category` is called and `deck_mutated` is emitted.
  - Trigger with a mock dialog that rejects → assert no service call.
- **Widget** (`tests/gui/test_main_window.py`):
  - Open `_AddCategoryDialog` with an empty name → OK button is disabled.
  - Enter a duplicate name → error label is visible, OK button is disabled.
  - Enter a valid name + slots → OK button is enabled; `.category_name` and
    `.slot_count` return the entered values.

## Critical files

- **Modified**: `src/deckslots/gui/main_window.py` (new `_AddCategoryDialog` class,
  wire `+ Category` action)
- **Tests**: `tests/gui/test_main_window.py`
