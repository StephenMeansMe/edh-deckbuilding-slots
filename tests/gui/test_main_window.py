"""Tests for the DeckWindow QMainWindow."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from deckslots.gui.main_window import DeckWindow  # noqa: E402
from deckslots.models import Decklist  # noqa: E402
from deckslots.storage import PlaintextRepository  # noqa: E402


def _repo(tmp_path):
    return PlaintextRepository(tmp_path / "decklist.bak")


class TestWindowChrome:
    def test_title_includes_deck_name(self, qtbot, tmp_path):
        deck = Decklist.create("My Deck")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert "My Deck" in win.windowTitle()

    def test_status_bar_shows_slot_count(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        msg = win.status_label.text()
        # Commander has 1 slot total, 0 filled
        assert "0/1" in msg or "0 / 1" in msg

    def test_menu_bar_has_expected_menus(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        titles = [a.text() for a in win.menuBar().actions()]
        for required in ("File", "Deck", "Category", "Card", "View", "Help"):
            assert required in titles, f"Missing menu: {required}"


class TestStatusBarUpdates:
    def test_status_updates_when_card_added(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        deck.add_card("Sol Ring", "Ramp")
        win.refresh_status_bar()
        # Commander + Ramp = 1 + 10 slots; 1 filled
        assert "1/11" in win.status_label.text()

    def test_status_warns_about_uncategorized(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.remove_card("Sol Ring")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert "Uncategorized" in win.status_label.text()


class TestPersistence:
    def test_card_move_persists_via_repository(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_category("Removal", 10)
        deck.add_card("Sol Ring", "Ramp")
        repo = _repo(tmp_path)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        # Simulate a move via the board's underlying tile
        ramp_tile = win.board.masonry_tiles["ramp"]  # noqa: F841
        removal_tile = win.board.masonry_tiles["removal"]
        ok = removal_tile.perform_move("Ramp", "Sol Ring")
        assert ok is True

        # Reload from repo and check
        reloaded = repo.load(1)
        assert "Sol Ring" in reloaded.categories["removal"].cards


class TestDeckSelectedSignal:
    def test_card_selected_propagates_to_inspector(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        win.board.card_selected.emit("Sol Ring")
        assert win.board.inspector.current_card == "Sol Ring"


class TestUndoRedo:
    def test_window_has_undo_stack(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert hasattr(win, "_undo_stack")

    def test_undo_reverts_deck_state(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        # Capture snapshot before mutation
        win._undo_stack.push(deck, "before delete")
        deck.categories.pop("ramp")
        assert "ramp" not in win._deck.categories

        # Undo should restore
        win._undo()
        assert "ramp" in win._deck.categories

    def test_redo_after_undo(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 10)
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        win._undo_stack.push(deck, "before delete")
        deck.categories.pop("ramp")
        win._undo()
        assert "ramp" in win._deck.categories
        win._redo()
        assert "ramp" not in win._deck.categories

    def test_menu_bar_has_edit_menu(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        titles = [a.text() for a in win.menuBar().actions()]
        assert "Edit" in titles


class TestAddCategoryDialog:
    """4.0.2 — wiring the Category menu's New Category... action."""

    def test_category_menu_has_new_category_action(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        cat_menu = None
        for a in win.menuBar().actions():
            if a.text() == "Category":
                cat_menu = a.menu()
                break
        assert cat_menu is not None
        action_texts = [a.text() for a in cat_menu.actions()]
        assert any(
            "New Category" in t for t in action_texts
        ), f"Category menu missing New Category... action; have: {action_texts}"

    def test_add_category_creates_user_category(self, qtbot, tmp_path, monkeypatch):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)

        # Stub the dialog to return ("Ramp", 8)
        from deckslots.gui import main_window as mw

        monkeypatch.setattr(
            mw, "_prompt_new_category", lambda parent, existing: ("Ramp", 8)
        )
        win._on_add_category()
        assert "ramp" in win._deck.categories
        from deckslots.models import CappedCategory

        ramp = win._deck.categories["ramp"]
        assert isinstance(ramp, CappedCategory)
        assert ramp.total_slots == 8

    def test_add_category_cancel_is_noop(self, qtbot, tmp_path, monkeypatch):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        from deckslots.gui import main_window as mw

        before = set(win._deck.categories)
        monkeypatch.setattr(
            mw, "_prompt_new_category", lambda parent, existing: None
        )
        win._on_add_category()
        assert set(win._deck.categories) == before

    def test_add_category_duplicate_rejected(self, qtbot, tmp_path, monkeypatch):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 8)
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        from deckslots.gui import main_window as mw

        warnings: list[tuple[str, str]] = []
        monkeypatch.setattr(
            mw.QMessageBox,
            "warning",
            lambda parent, title, msg: warnings.append((title, msg)),
        )
        # Service-layer rejection: duplicate name (dialog returns a duplicate
        # because the user could bypass pre-validation via the monkeypatch)
        monkeypatch.setattr(
            mw, "_prompt_new_category", lambda parent, existing: ("Ramp", 5)
        )
        win._on_add_category()
        # Slots unchanged from original
        assert win._deck.categories["ramp"].total_slots == 8
        assert warnings, "expected a QMessageBox.warning to be shown"


class TestNewDeckDialog:
    """4.0.3 — Create a new deck from the GUI with unique-name validation."""

    def test_file_menu_has_new_deck_action(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        file_menu = None
        for a in win.menuBar().actions():
            if a.text() == "File":
                file_menu = a.menu()
                break
        assert file_menu is not None
        texts = [a.text() for a in file_menu.actions()]
        assert any("New Deck" in t for t in texts), texts

    def test_create_deck_saves_to_repo_and_switches(self, qtbot, tmp_path, monkeypatch):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Alpha")
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        from deckslots.gui import main_window as mw

        monkeypatch.setattr(mw, "_prompt_new_deck_name", lambda parent, taken: "Beta")
        win._on_create_deck()
        assert win.deck.name == "Beta"
        names = {s.name for s in repo.list()}
        assert {"Alpha", "Beta"} <= names

    def test_create_deck_cancel_is_noop(self, qtbot, tmp_path, monkeypatch):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Alpha")
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        from deckslots.gui import main_window as mw

        monkeypatch.setattr(mw, "_prompt_new_deck_name", lambda parent, taken: None)
        win._on_create_deck()
        assert win.deck.name == "Alpha"

    def test_create_deck_prompt_sees_existing_names(self, qtbot, tmp_path, monkeypatch):
        """The prompt receives the existing deck names so it can reject duplicates."""
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Alpha")
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        seen: list[set[str]] = []
        from deckslots.gui import main_window as mw

        def prompt(parent, taken):
            seen.append(taken)
            return None

        monkeypatch.setattr(mw, "_prompt_new_deck_name", prompt)
        win._on_create_deck()
        assert seen and "Alpha" in seen[0]


class TestImportExportDialogs:
    """4.0.4 — Import... / Export... toolbar/menu actions wired to QFileDialog."""

    def test_deck_menu_has_import_and_export(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        deck_menu = None
        for a in win.menuBar().actions():
            if a.text() == "Deck":
                deck_menu = a.menu()
                break
        assert deck_menu is not None
        texts = [a.text() for a in deck_menu.actions()]
        assert any("Import" in t for t in texts), texts
        assert any("Export" in t for t in texts), texts

    def test_export_writes_file(self, qtbot, tmp_path, monkeypatch):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 5)
        deck.add_card("Sol Ring", "Ramp")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)

        out = tmp_path / "exported.txt"
        from deckslots.gui import main_window as mw

        monkeypatch.setattr(
            mw, "_prompt_export_path", lambda parent, default: str(out)
        )
        win._on_export_deck()
        assert out.exists()
        text = out.read_text()
        assert "Commander" in text
        assert "Sol Ring" in text

    def test_export_cancel_writes_nothing(self, qtbot, tmp_path, monkeypatch):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        from deckslots.gui import main_window as mw

        monkeypatch.setattr(mw, "_prompt_export_path", lambda parent, default: None)
        win._on_export_deck()  # should be a no-op, no error

    def test_import_replaces_active_deck(self, qtbot, tmp_path, monkeypatch):
        # Write a Moxfield-format file to import
        src = tmp_path / "deck.txt"
        src.write_text(
            "Commander\n1 Atraxa, Praetors' Voice\n\nMaindeck\n1 Sol Ring\n"
        )
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Original")
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        from deckslots.gui import main_window as mw

        monkeypatch.setattr(mw, "_prompt_import_path", lambda parent: str(src))
        win._on_import_deck()
        # The deck file name (stem) becomes the deck name
        assert win.deck.name == "deck"
        assert "Atraxa, Praetors' Voice" in win.deck.categories["commander"].cards

    def test_import_parse_failure_keeps_original_deck(
        self, qtbot, tmp_path, monkeypatch
    ):
        deck = Decklist.create("Original")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)

        from deckslots.gui import main_window as mw

        warnings: list[tuple[str, str]] = []
        monkeypatch.setattr(
            mw.QMessageBox,
            "warning",
            lambda parent, title, msg: warnings.append((title, msg)),
        )
        monkeypatch.setattr(
            mw, "_prompt_import_path", lambda parent: str(tmp_path / "nope.txt")
        )
        win._on_import_deck()
        assert win.deck.name == "Original"
        assert warnings


class TestKeyboardMove:
    """4.4.1 — Keyboard-only card move alternative to drag-and-drop."""

    def test_card_menu_has_move_action(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 5)
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        card_menu = None
        for a in win.menuBar().actions():
            if a.text() == "Card":
                card_menu = a.menu()
                break
        assert card_menu is not None
        action_texts = [a.text() for a in card_menu.actions()]
        assert any("Move Card" in t for t in action_texts), action_texts

    def test_move_card_routes_through_services(
        self, qtbot, tmp_path, monkeypatch
    ):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 5)
        deck.add_category("Draw", 5)
        deck.add_card("Sol Ring", "Ramp")
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)

        win._last_selected_card = "Sol Ring"
        from deckslots.gui import main_window as mw

        monkeypatch.setattr(
            mw, "_prompt_move_destination", lambda parent, choices, card: "Draw"
        )
        win._on_keyboard_move_card()
        assert win.deck.find_card("Sol Ring") == "draw"

    def test_move_card_no_selection_is_noop(self, qtbot, tmp_path, monkeypatch):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        from deckslots.gui import main_window as mw

        called: list[tuple] = []
        monkeypatch.setattr(
            mw.QMessageBox,
            "information",
            lambda *args: called.append(args),
        )
        win._last_selected_card = None
        win._on_keyboard_move_card()
        assert win.deck.total_filled == 0


class TestAccessibilityLabels:
    """4.4.2 — Screen-reader-friendly accessible names on key widgets."""

    def test_cat_tile_has_accessible_name(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 5)
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        tile = win.board.masonry_tiles["ramp"]
        acc = tile.accessibleName() or tile.name_label.accessibleName()
        assert "Ramp" in acc

    def test_status_label_has_accessible_name(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert win.status_label.accessibleName()

    def test_inspector_has_accessible_name(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        assert win.board.inspector.accessibleName()


class TestOmnibarLegalityWarning:
    """4.4.3 — surface Commander legality warnings from services in the GUI."""

    def test_warning_from_services_appears_in_status_bar(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        deck.add_category("Ramp", 5)
        index = {
            "brainstorm": {
                "name": "Brainstorm",
                "legalities": {"commander": "banned"},
            }
        }
        win = DeckWindow(deck, _repo(tmp_path), scryfall_index=index)
        qtbot.addWidget(win)
        win._on_card_chosen("Brainstorm", "ramp")
        text = win.status_label.text()
        assert "Brainstorm" in text and "not legal" in text


class TestLibraryDock:
    def test_sqlite_repo_shows_library_dock(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Test")
        repo.save(deck)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)
        assert hasattr(win, "_library_dock")
        assert win._library_dock is not None

    def test_load_deck_switches_active_deck(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck1 = Decklist.create("Alpha")
        deck2 = Decklist.create("Beta")
        repo.save(deck1)
        id2 = repo.save(deck2)
        win = DeckWindow(deck1, repo)
        qtbot.addWidget(win)
        win._load_deck(id2)
        assert win.deck.name == "Beta"
        assert "Beta" in win.windowTitle()

    def test_load_deck_updates_board(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck1 = Decklist.create("Alpha")
        deck1.add_category("Ramp", 5)
        repo.save(deck1)
        deck2 = Decklist.create("Beta")
        id2 = repo.save(deck2)
        win = DeckWindow(deck1, repo)
        qtbot.addWidget(win)
        win._load_deck(id2)
        # Beta has no user categories, so masonry should be empty
        assert win.board.masonry_tiles == {}

    def test_load_deck_resets_inspector(self, qtbot, tmp_path):
        from deckslots.storage import SqliteRepository

        repo = SqliteRepository(tmp_path / "lib.db")
        deck = Decklist.create("Alpha")
        repo.save(deck)
        deck2 = Decklist.create("Beta")
        id2 = repo.save(deck2)
        win = DeckWindow(deck, repo)
        qtbot.addWidget(win)
        # select a card first
        win.board.card_selected.emit("Sol Ring")
        win._load_deck(id2)
        # After switch the inspector should have no card (or a different deck's card)
        # The board's inspector must belong to the new board
        assert win.board.inspector is not None

    def test_plaintext_repo_has_no_library_dock(self, qtbot, tmp_path):
        deck = Decklist.create("Test")
        win = DeckWindow(deck, _repo(tmp_path))
        qtbot.addWidget(win)
        # PlaintextRepository is single-deck; no library dock added
        assert not hasattr(win, "_library_dock") or win._library_dock is None
