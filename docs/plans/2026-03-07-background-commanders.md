# Background Commanders Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `decklist enable-background` / `disable-background` / `disable-partners`, a `commander_overcrowded` persistent warning, and update save/load to use dynamic Commander slot allocation instead of mode tags.

**Architecture:** Mirrors the existing partners implementation exactly. `Decklist` gets `background_enabled: bool`, `enable_background()`, `disable_background()`, and `disable_partners()`. `enable_partners()` is changed to be additive (`+= 1`) rather than setting an absolute value, so both modes can coexist. `_format_save_file` drops the `Commander [partners]` tag; `_parse_save_file` ignores mode tags and sets Commander's slot count from the number of loaded cards. `repl.py` gets a second persistent warning for `commander_overcrowded`.

**Tech Stack:** Python 3.12, pytest, scrut (functional CLI tests). Run tests with `uv run pytest` and `scrut test --work-directory . tests/functional/`.

---

### Task 1: Make `enable_partners()` additive and add `enable_background()`

This is the foundation. `enable_partners()` must increment (not set) Commander slots so that enabling both modes gives 3 slots.

**Files:**
- Modify: `src/deckslots/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing tests**

Add this class after `TestDecklistPartners` in `tests/test_models.py`:

```python
class TestDecklistBackground:
    """Decklist.enable_background allows a Background alongside the commander."""

    def test_new_decklist_has_background_disabled(self):
        """A freshly created decklist has background_enabled set to False."""
        deck = Decklist.create("Test Deck")
        assert deck.background_enabled is False

    def test_enable_background_sets_flag(self):
        """enable_background sets background_enabled to True."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        assert deck.background_enabled is True

    def test_enable_background_expands_commander_to_two_slots(self):
        """enable_background sets the Commander category's total_slots to 2."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        assert deck.categories["commander"].total_slots == 2

    def test_enable_background_allows_two_commanders(self):
        """After enable_background, two cards can be added to Commander."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert len(deck.categories["commander"].cards) == 2

    def test_enable_background_is_idempotent(self):
        """Calling enable_background twice keeps Commander at 2 slots."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.enable_background()
        assert deck.categories["commander"].total_slots == 2
        assert deck.background_enabled is True

    def test_both_modes_enabled_gives_three_slots(self):
        """Enabling partners and background gives Commander 3 slots."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        assert deck.categories["commander"].total_slots == 3

    def test_both_modes_allows_three_commanders(self):
        """With both modes enabled, three cards can be added to Commander."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Livaan, Cultist of Tiamat", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert len(deck.categories["commander"].cards) == 3
```

Also update `test_enable_partners_is_idempotent` in `TestDecklistPartners` — it currently calls `enable_partners()` twice. With the new additive implementation, the guard must hold. The test body does not change; just verify it still passes.

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_models.py::TestDecklistBackground -v
```

Expected: FAIL — `Decklist` has no `background_enabled` attribute.

**Step 3: Write minimal implementation**

In `src/deckslots/models.py`, update `Decklist`:

```python
@dataclass
class Decklist:
    name: str
    categories: dict[str, Category] = field(default_factory=dict)
    partners_enabled: bool = False
    background_enabled: bool = False
```

Replace `enable_partners()` body with an additive, guarded version:

```python
def enable_partners(self) -> None:
    """Allow two commanders by expanding the Commander category by 1 slot."""
    if self.partners_enabled:
        return
    self.partners_enabled = True
    commander = self.categories["commander"]
    assert isinstance(commander, CappedCategory)
    commander.total_slots += 1
```

Add `enable_background()` immediately after:

```python
def enable_background(self) -> None:
    """Allow a Background alongside the commander by expanding Commander by 1 slot."""
    if self.background_enabled:
        return
    self.background_enabled = True
    commander = self.categories["commander"]
    assert isinstance(commander, CappedCategory)
    commander.total_slots += 1
```

**Step 4: Run all model tests**

```bash
uv run pytest tests/test_models.py -v
```

Expected: all pass (the existing `test_enable_partners_expands_commander_to_two_slots` still passes because 1 + 1 = 2).

**Step 5: Commit**

```bash
git add src/deckslots/models.py tests/test_models.py
git commit -m "feat: add background_enabled flag and enable_background() method"
```

---

### Task 2: Add `disable_partners()` and `disable_background()` model methods

Disabling a mode decrements Commander's slot count and moves **all** Commander cards to Uncategorized.

**Files:**
- Modify: `src/deckslots/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing tests**

Add after `TestDecklistBackground` in `tests/test_models.py`:

```python
class TestDecklistDisableModes:
    """disable_partners and disable_background reverse their respective enable calls."""

    def test_disable_partners_clears_flag(self):
        """disable_partners sets partners_enabled to False."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.disable_partners()
        assert deck.partners_enabled is False

    def test_disable_partners_decrements_commander_slots(self):
        """disable_partners shrinks Commander back to 1 slot (when background is off)."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.disable_partners()
        assert deck.categories["commander"].total_slots == 1

    def test_disable_partners_moves_all_commanders_to_uncategorized(self):
        """disable_partners moves every Commander card to Uncategorized."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        deck.disable_partners()
        assert deck.categories["commander"].cards == []
        assert "Malcolm, Keen-Eyed Navigator" in deck.categories["uncategorized"].cards
        assert "Tana, the Bloodsower" in deck.categories["uncategorized"].cards

    def test_disable_partners_creates_uncategorized_if_needed(self):
        """disable_partners creates the Uncategorized category if it does not exist."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        assert "uncategorized" not in deck.categories
        deck.disable_partners()
        assert "uncategorized" in deck.categories

    def test_disable_partners_is_noop_when_already_disabled(self):
        """disable_partners does nothing when partners_enabled is already False."""
        deck = Decklist.create("Test Deck")
        deck.disable_partners()  # should not raise
        assert deck.categories["commander"].total_slots == 1

    def test_disable_background_clears_flag(self):
        """disable_background sets background_enabled to False."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.disable_background()
        assert deck.background_enabled is False

    def test_disable_background_decrements_commander_slots(self):
        """disable_background shrinks Commander back to 1 slot (when partners is off)."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.disable_background()
        assert deck.categories["commander"].total_slots == 1

    def test_disable_background_moves_all_commanders_to_uncategorized(self):
        """disable_background moves every Commander card to Uncategorized."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Criminal Past", "Commander")
        deck.disable_background()
        assert deck.categories["commander"].cards == []
        assert "Cloakwood Hermit" in deck.categories["uncategorized"].cards
        assert "Criminal Past" in deck.categories["uncategorized"].cards

    def test_disable_one_mode_with_both_enabled_leaves_two_slots(self):
        """Disabling one mode when both are on leaves Commander with 2 slots."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        deck.disable_partners()
        assert deck.categories["commander"].total_slots == 2
        assert deck.partners_enabled is False
        assert deck.background_enabled is True
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_models.py::TestDecklistDisableModes -v
```

Expected: FAIL — `disable_partners` / `disable_background` do not exist.

**Step 3: Write minimal implementation**

Add after `enable_background()` in `models.py`:

```python
def disable_partners(self) -> None:
    """Disable partners mode, moving all Commander cards to Uncategorized."""
    if not self.partners_enabled:
        return
    self.partners_enabled = False
    commander = self.categories["commander"]
    assert isinstance(commander, CappedCategory)
    commander.total_slots -= 1
    self._evacuate_commander()

def disable_background(self) -> None:
    """Disable background mode, moving all Commander cards to Uncategorized."""
    if not self.background_enabled:
        return
    self.background_enabled = False
    commander = self.categories["commander"]
    assert isinstance(commander, CappedCategory)
    commander.total_slots -= 1
    self._evacuate_commander()

def _evacuate_commander(self) -> None:
    """Move all Commander cards to Uncategorized."""
    if "uncategorized" not in self.categories:
        self.categories["uncategorized"] = UncappedCategory(
            name="Uncategorized", fixed=True, user_addable=False
        )
    commander = self.categories["commander"]
    for card in list(commander.cards):
        commander.cards.remove(card)
        self.categories["uncategorized"].cards.append(card)
```

**Step 4: Run all model tests**

```bash
uv run pytest tests/test_models.py -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/deckslots/models.py tests/test_models.py
git commit -m "feat: add disable_partners() and disable_background() with card evacuation"
```

---

### Task 3: Add `commander_overcrowded` property

**Files:**
- Modify: `src/deckslots/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing tests**

Add after `TestDecklistDisableModes` in `tests/test_models.py`:

```python
class TestCommanderOvercrowded:
    """Decklist.commander_overcrowded detects too many cards for enabled modes."""

    def test_empty_commander_not_overcrowded(self):
        """Commander with no cards is never overcrowded."""
        deck = Decklist.create("Test Deck")
        assert deck.commander_overcrowded is False

    def test_one_card_no_modes_not_overcrowded(self):
        """One Commander card with no modes enabled is normal."""
        deck = Decklist.create("Test Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        assert deck.commander_overcrowded is False

    def test_two_cards_no_modes_is_overcrowded(self):
        """Two Commander cards with no modes enabled is overcrowded."""
        deck = Decklist.create("Test Deck")
        # Bypass add_card to force the overcrowded state (e.g. after a load)
        deck.categories["commander"].total_slots = 2
        deck.categories["commander"].cards = [
            "Cloakwood Hermit",
            "Criminal Past",
        ]
        assert deck.commander_overcrowded is True

    def test_two_cards_partners_enabled_not_overcrowded(self):
        """Two Commander cards with partners enabled is fine."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        assert deck.commander_overcrowded is False

    def test_two_cards_background_enabled_not_overcrowded(self):
        """Two Commander cards with background enabled is fine."""
        deck = Decklist.create("Test Deck")
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert deck.commander_overcrowded is False

    def test_three_cards_one_mode_is_overcrowded(self):
        """Three Commander cards with only one mode enabled is overcrowded."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.categories["commander"].total_slots = 3
        deck.categories["commander"].cards = ["A", "B", "C"]
        assert deck.commander_overcrowded is True

    def test_three_cards_both_modes_not_overcrowded(self):
        """Three Commander cards with both modes enabled is fine."""
        deck = Decklist.create("Test Deck")
        deck.enable_partners()
        deck.enable_background()
        deck.add_card("Cloakwood Hermit", "Commander")
        deck.add_card("Livaan, Cultist of Tiamat", "Commander")
        deck.add_card("Criminal Past", "Commander")
        assert deck.commander_overcrowded is False
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_models.py::TestCommanderOvercrowded -v
```

Expected: FAIL — `Decklist` has no `commander_overcrowded` attribute.

**Step 3: Write minimal implementation**

Add after `rename()` in `Decklist` (before `create()`):

```python
@property
def commander_overcrowded(self) -> bool:
    """True when Commander holds more cards than enabled modes allow."""
    commander = self.categories.get("commander")
    if commander is None:
        return False
    max_allowed = 1 + self.partners_enabled + self.background_enabled
    return len(commander.cards) > max_allowed
```

**Step 4: Run all model tests**

```bash
uv run pytest tests/test_models.py -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/deckslots/models.py tests/test_models.py
git commit -m "feat: add commander_overcrowded property to Decklist"
```

---

### Task 4: Update save/load — drop mode tag, dynamic Commander slot allocation

The save format will always write plain `Commander`. On load, the `Commander [partners]` tag (and any future tags) are silently ignored; Commander's slot count is set from the number of loaded cards.

This resolves issue #42 and provides backwards compatibility.

**Files:**
- Modify: `src/deckslots/commands.py`
- Test: `tests/test_commands.py`

**Step 1: Update existing tests that will break**

Find `TestFormatSaveFilePartners` in `tests/test_commands.py`. Update these two tests:

```python
# OLD — remove this test entirely (behaviour no longer applies):
# test_partners_enabled_uses_partners_heading

# REPLACE with:
def test_save_always_uses_plain_commander_heading(self):
    """Commander section heading is always plain 'Commander' regardless of mode."""
    deck_solo = Decklist.create("Solo Deck")
    assert "Commander" in _format_save_file(deck_solo)
    assert "Commander [partners]" not in _format_save_file(deck_solo)

    deck_partners = Decklist.create("Partner Deck")
    deck_partners.enable_partners()
    assert "Commander" in _format_save_file(deck_partners)
    assert "Commander [partners]" not in _format_save_file(deck_partners)

# UPDATE test_parse_save_file_restores_partners_enabled:
def test_load_ignores_partners_tag_and_dynamically_allocates_slots(self, tmp_path):
    """Loading a file with 'Commander [partners]' ignores the tag;
    Commander slots are set from the number of loaded cards."""
    content = "# Partner Deck\n\nCommander [partners]\n1 Malcolm, Keen-Eyed Navigator\n1 Tana, the Bloodsower\n\nBasic Lands\n"
    path = tmp_path / "deck.bak"
    path.write_text(content)
    loaded = _parse_save_file(str(path))
    assert loaded.partners_enabled is False   # tag is ignored
    assert loaded.categories["commander"].total_slots == 2  # dynamic
    assert "Malcolm, Keen-Eyed Navigator" in loaded.categories["commander"].cards
    assert "Tana, the Bloodsower" in loaded.categories["commander"].cards
```

Also add new tests to `TestFormatSaveFilePartners`:

```python
def test_load_sets_commander_slots_from_card_count(self, tmp_path):
    """Loading a plain Commander section with 2 cards sets total_slots to 2."""
    content = "# My Deck\n\nCommander\n1 Malcolm, Keen-Eyed Navigator\n1 Tana, the Bloodsower\n\nBasic Lands\n"
    path = tmp_path / "deck.bak"
    path.write_text(content)
    loaded = _parse_save_file(str(path))
    assert loaded.categories["commander"].total_slots == 2
    assert loaded.partners_enabled is False

def test_load_with_one_commander_keeps_one_slot(self, tmp_path):
    """Loading a Commander section with 1 card keeps total_slots at 1."""
    deck = Decklist.create("Solo Deck")
    deck.add_card("Atraxa, Praetors' Voice", "Commander")
    path = tmp_path / "deck.bak"
    path.write_text(_format_save_file(deck))
    loaded = _parse_save_file(str(path))
    assert loaded.categories["commander"].total_slots == 1
```

**Step 2: Run the updated tests to verify they fail**

```bash
uv run pytest tests/test_commands.py::TestFormatSaveFilePartners -v
```

Expected: some tests fail (save still writes `[partners]`; load still calls `enable_partners()`).

**Step 3: Update `_format_save_file`**

In `commands.py`, replace the Commander heading block:

```python
# OLD:
if cat.name == "Commander":
    heading = (
        "Commander [partners]" if decklist.partners_enabled else "Commander"
    )

# NEW:
if cat.name == "Commander":
    heading = "Commander"
```

**Step 4: Update `_parse_save_file`**

Replace the two Commander-heading branches with a single one:

```python
# OLD:
if s == "Commander":
    current_category = "Commander"
    continue
if s == "Commander [partners]":
    deck.enable_partners()
    current_category = "Commander"
    continue

# NEW:
if s == "Commander" or s.startswith("Commander ["):
    current_category = "Commander"
    continue
```

Then, after the main loop (before `return deck`), add dynamic slot allocation:

```python
# Dynamically set Commander slots from loaded card count
commander_cat = deck.categories.get("commander")
if commander_cat is not None and isinstance(commander_cat, CappedCategory):
    commander_cat.total_slots = max(1, len(commander_cat.cards))
```

**Note:** The cards are added via `deck.add_card(card, current_category)` in the loop. Because Commander's default `total_slots` is 1, the second card will be rejected by the fullness check. Fix this by temporarily setting Commander's `total_slots` to 99 at the start of `_parse_save_file`, then correcting it after the loop:

Find the line `deck = Decklist.create(name)` and add the temporary expansion right after:

```python
deck = Decklist.create(name)
# Temporarily expand Commander to accept any number of cards during load;
# the correct slot count is set after all cards are read.
commander_cat = deck.categories["commander"]
assert isinstance(commander_cat, CappedCategory)
commander_cat.total_slots = 99
```

**Step 5: Run all command tests**

```bash
uv run pytest tests/test_commands.py -v
```

Expected: all pass.

**Step 6: Commit**

```bash
git add src/deckslots/commands.py tests/test_commands.py
git commit -m "refactor: drop Commander mode tags from save format; dynamic slot allocation on load (closes #42)"
```

---

### Task 5: Add command handlers — `enable-background`, `disable-partners`, `disable-background`

**Files:**
- Modify: `src/deckslots/commands.py`
- Test: `tests/test_commands.py`

**Step 1: Write the failing tests**

Add three test classes after `TestHandleDecklistEnablePartners` in `tests/test_commands.py`. Use the same `_cmd()` helper pattern as that class.

```python
class TestHandleDecklistEnableBackground:
    """handle_decklist_enable_background enables background commanders."""

    def _cmd(self) -> ParsedCommand:
        return ParsedCommand(
            kind="object_verb",
            raw="decklist enable-background",
            obj="decklist",
            verb="enable-background",
            args=[],
        )

    def test_returns_error_when_no_active_decklist(self):
        session = Session()
        result = handle_decklist_enable_background(session, self._cmd())
        assert "No active decklist" in result

    def test_sets_background_enabled_on_decklist(self):
        session = _make_session_with_deck()
        handle_decklist_enable_background(session, self._cmd())
        assert session.decklist.background_enabled is True

    def test_commander_category_has_two_slots_after_enable(self):
        session = _make_session_with_deck()
        handle_decklist_enable_background(session, self._cmd())
        assert session.decklist.categories["commander"].total_slots == 2

    def test_returns_confirmation_message(self):
        session = _make_session_with_deck()
        result = handle_decklist_enable_background(session, self._cmd())
        assert "background" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "enable-background") in registry


class TestHandleDecklistDisablePartners:
    """handle_decklist_disable_partners disables partner mode and evacuates commanders."""

    def _cmd(self) -> ParsedCommand:
        return ParsedCommand(
            kind="object_verb",
            raw="decklist disable-partners",
            obj="decklist",
            verb="disable-partners",
            args=[],
        )

    def test_returns_error_when_no_active_decklist(self):
        session = Session()
        result = handle_decklist_disable_partners(session, self._cmd())
        assert "No active decklist" in result

    def test_clears_partners_enabled(self):
        session = _make_session_with_deck()
        session.decklist.enable_partners()
        handle_decklist_disable_partners(session, self._cmd())
        assert session.decklist.partners_enabled is False

    def test_commander_cards_move_to_uncategorized(self):
        session = _make_session_with_deck()
        session.decklist.enable_partners()
        session.decklist.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        session.decklist.add_card("Tana, the Bloodsower", "Commander")
        handle_decklist_disable_partners(session, self._cmd())
        assert session.decklist.categories["commander"].cards == []
        assert "Malcolm, Keen-Eyed Navigator" in session.decklist.categories["uncategorized"].cards

    def test_returns_confirmation_message(self):
        session = _make_session_with_deck()
        session.decklist.enable_partners()
        result = handle_decklist_disable_partners(session, self._cmd())
        assert "uncategorized" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "disable-partners") in registry


class TestHandleDecklistDisableBackground:
    """handle_decklist_disable_background disables background mode and evacuates commanders."""

    def _cmd(self) -> ParsedCommand:
        return ParsedCommand(
            kind="object_verb",
            raw="decklist disable-background",
            obj="decklist",
            verb="disable-background",
            args=[],
        )

    def test_returns_error_when_no_active_decklist(self):
        session = Session()
        result = handle_decklist_disable_background(session, self._cmd())
        assert "No active decklist" in result

    def test_clears_background_enabled(self):
        session = _make_session_with_deck()
        session.decklist.enable_background()
        handle_decklist_disable_background(session, self._cmd())
        assert session.decklist.background_enabled is False

    def test_commander_cards_move_to_uncategorized(self):
        session = _make_session_with_deck()
        session.decklist.enable_background()
        session.decklist.add_card("Cloakwood Hermit", "Commander")
        session.decklist.add_card("Criminal Past", "Commander")
        handle_decklist_disable_background(session, self._cmd())
        assert session.decklist.categories["commander"].cards == []
        assert "Cloakwood Hermit" in session.decklist.categories["uncategorized"].cards

    def test_returns_confirmation_message(self):
        session = _make_session_with_deck()
        session.decklist.enable_background()
        result = handle_decklist_disable_background(session, self._cmd())
        assert "uncategorized" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "disable-background") in registry
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_commands.py::TestHandleDecklistEnableBackground tests/test_commands.py::TestHandleDecklistDisablePartners tests/test_commands.py::TestHandleDecklistDisableBackground -v
```

Expected: FAIL — handlers do not exist.

**Step 3: Write the handlers**

In `commands.py`, add after `handle_decklist_enable_partners`:

```python
def handle_decklist_enable_background(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    session.decklist.enable_background()
    return "Background mode enabled. The Commander category now has 2 slots."


def handle_decklist_disable_partners(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    session.decklist.disable_partners()
    return "Partners mode disabled. All commanders moved to Uncategorized."


def handle_decklist_disable_background(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    session.decklist.disable_background()
    return "Background mode disabled. All commanders moved to Uncategorized."
```

Register all three in `register_all_handlers`:

```python
("decklist", "enable-background"): lambda cmd: handle_decklist_enable_background(session, cmd),
("decklist", "disable-partners"): lambda cmd: handle_decklist_disable_partners(session, cmd),
("decklist", "disable-background"): lambda cmd: handle_decklist_disable_background(session, cmd),
```

Also update the imports in `tests/test_commands.py` to include the three new handler names.

**Step 4: Run all tests**

```bash
uv run pytest -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/deckslots/commands.py tests/test_commands.py
git commit -m "feat: add enable-background, disable-partners, disable-background handlers"
```

---

### Task 6: Add `enable-background` and disable commands to help text

**Files:**
- Modify: `src/deckslots/commands.py`
- Test: `tests/test_commands.py`

**Step 1: Write the failing test**

Find the existing `TestHandleHelp` class in `tests/test_commands.py`. Add:

```python
def test_help_includes_enable_background(self):
    result = handle_help()
    assert "enable-background" in result

def test_help_includes_disable_partners(self):
    result = handle_help()
    assert "disable-partners" in result

def test_help_includes_disable_background(self):
    result = handle_help()
    assert "disable-background" in result
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_commands.py::TestHandleHelp -v
```

Expected: the three new tests fail.

**Step 3: Update help text**

In `handle_help()`, add after the `enable-partners` line:

```python
"  decklist enable-background    Allow a Background commander (Choose a Background)",
"  decklist disable-partners     Disable partner mode; moves all commanders to Uncategorized",
"  decklist disable-background   Disable background mode; moves all commanders to Uncategorized",
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_commands.py::TestHandleHelp -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/deckslots/commands.py tests/test_commands.py
git commit -m "feat: add enable-background and disable commands to help text"
```

---

### Task 7: Add persistent `commander_overcrowded` warning in `repl.py`

**Files:**
- Modify: `src/deckslots/repl.py`
- Test: `tests/test_functional.py` (the pytest-based functional runner)

**Step 1: Write the failing test**

In `tests/test_functional.py`, find how the Uncategorized warning test is written and add a parallel one for `commander_overcrowded`. Look at the existing test patterns. Add:

```python
def test_commander_overcrowded_warning_appears(tmp_path):
    """Persistent warning appears when Commander has more cards than modes allow."""
    # Force an overcrowded state by writing a save file with 2 Commander cards,
    # no mode enabled. On load, Commander gets 2 slots dynamically but no mode
    # flag is set, so commander_overcrowded is True.
    save = tmp_path / "deckslots" / "decklist.bak"
    save.parent.mkdir(parents=True)
    save.write_text("# My Deck\n\nCommander\n1 Cloakwood Hermit\n1 Criminal Past\n\nBasic Lands\n")
    result = subprocess.run(
        ["uv", "run", "deckslots"],
        input="show\nquit\n",
        capture_output=True,
        text=True,
        env={**os.environ, "XDG_STATE_HOME": str(tmp_path)},
    )
    assert "Warning" in result.stdout
    assert "Commander" in result.stdout
    assert "overcrowded" in result.stdout.lower() or "more cards" in result.stdout.lower()
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_functional.py -k "overcrowded" -v
```

Expected: FAIL — no such warning appears.

**Step 3: Add the warning to `repl.py`**

In `repl.py`, after the existing Uncategorized warning block (lines 85–96), add:

```python
if (
    session.decklist is not None
    and session.decklist.commander_overcrowded
):
    warning = (
        "Warning: Commander has more cards than enabled modes allow. "
        "Run 'decklist enable-partners' or 'decklist enable-background', "
        "or use 'card move' to reassign the extra cards."
    )
    result = f"{warning}\n{result}"
```

**Step 4: Run all tests**

```bash
uv run pytest -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add src/deckslots/repl.py tests/test_functional.py
git commit -m "feat: add persistent warning when Commander is overcrowded"
```

---

### Task 8: Scrut functional CLI tests

**Files:**
- Create: `tests/functional/12-background.md`

**Step 1: Write the tests**

Create `tests/functional/12-background.md`:

````markdown
# Background Commanders

## decklist enable-background allows two commanders

```scrut
$ printf 'decklist create BgDeck\ndecklist enable-background\ncard add Commander Cloakwood Hermit\ncard add Commander Criminal Past\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'BgDeck'.
deckslots> Background mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Cloakwood Hermit' to 'Commander'.
deckslots> Added 'Criminal Past' to 'Commander'.
deckslots> Decklist: BgDeck
Total slots: 2 (2 filled)
Categories:
  Commander: 2/2 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## decklist enable-background without active decklist shows error

```scrut
$ printf 'decklist enable-background\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## decklist disable-partners moves all commanders to Uncategorized

```scrut
$ printf 'decklist create PartnerDeck\ndecklist enable-partners\ncard add Commander Malcolm, Keen-Eyed Navigator\ncard add Commander Tana, the Bloodsower\ndecklist disable-partners\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'PartnerDeck'.
deckslots> Partners mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Malcolm, Keen-Eyed Navigator' to 'Commander'.
deckslots> Added 'Tana, the Bloodsower' to 'Commander'.
deckslots> Partners mode disabled. All commanders moved to Uncategorized.
Warning: 2 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
deckslots> Warning: 2 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Decklist: PartnerDeck
Total slots: 1 (0 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Uncategorized: 2 slots filled (uncapped)
deckslots> Goodbye.
```

## both modes enabled gives three Commander slots

```scrut
$ printf 'decklist create Hybrid\ndecklist enable-partners\ndecklist enable-background\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Hybrid'.
deckslots> Partners mode enabled. The Commander category now has 2 slots.
deckslots> Background mode enabled. The Commander category now has 2 slots.
deckslots> Decklist: Hybrid
Total slots: 3 (0 filled)
Categories:
  Commander: 0/3 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## overcrowded warning fires after loading a save with two commanders and no mode

```scrut
$ printf 'decklist create BgDeck\ndecklist enable-background\ncard add Commander Cloakwood Hermit\ncard add Commander Criminal Past\ndecklist save\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'BgDeck'.
deckslots> Background mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Cloakwood Hermit' to 'Commander'.
deckslots> Added 'Criminal Past' to 'Commander'.
deckslots> Saved 'BgDeck'.
deckslots> Goodbye.
```

```scrut
$ printf 'decklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
Resumed 'BgDeck'.
deckslots> Welcome to deckslots.
deckslots> Warning: Commander has more cards than enabled modes allow. Run 'decklist enable-partners' or 'decklist enable-background', or use 'card move' to reassign the extra cards.
Decklist: BgDeck
Total slots: 2 (2 filled)
Categories:
  Commander: 2/2 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```
````

**Step 2: Run the scrut tests to verify they fail**

```bash
scrut test --work-directory . tests/functional/12-background.md
```

Expected: failures — commands not yet showing correct output.

**Step 3: Fix output mismatches**

After all previous tasks are complete, the tests should pass. If the `enable-background` message says "2 slots" but Commander ends up with 3 when both modes are on, adjust the confirmation message to reflect the actual new total:

```python
def handle_decklist_enable_background(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    session.decklist.enable_background()
    slots = session.decklist.categories["commander"].total_slots
    return f"Background mode enabled. The Commander category now has {slots} slots."
```

Apply the same pattern to `handle_decklist_enable_partners`:

```python
def handle_decklist_enable_partners(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    session.decklist.enable_partners()
    slots = session.decklist.categories["commander"].total_slots
    return f"Partners mode enabled. The Commander category now has {slots} slots."
```

**Step 4: Run the full test suite**

```bash
uv run pytest && scrut test --work-directory . tests/functional/
```

Expected: all pass.

**Step 5: Commit**

```bash
git add tests/functional/12-background.md src/deckslots/commands.py
git commit -m "test: add scrut functional tests for Background commanders (12-background.md)"
```

---

### Task 9: Lint, type-check, final verification

**Step 1: Run linter**

```bash
uv run ruff check .
```

Fix any issues, then:

```bash
uv run ruff format .
```

**Step 2: Run type checker**

```bash
uv run ty check
```

Fix any type errors.

**Step 3: Run the full suite one final time**

```bash
uv run pytest && scrut test --work-directory . tests/functional/
```

Expected: all pass.

**Step 4: Commit any lint/type fixes**

```bash
git add -u
git commit -m "refactor: fix lint and type errors"
```
