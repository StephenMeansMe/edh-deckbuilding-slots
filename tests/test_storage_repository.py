"""Tests for the DecklistRepository protocol and PlaintextRepository."""


from deckslots.models import Decklist
from deckslots.storage import PlaintextRepository, _format_save_file, _get_save_path


def _full_deck() -> Decklist:
    """Return a Decklist exercising all category types."""
    deck = Decklist.create("Atraxa Stax")
    deck.add_card("Atraxa, Praetors' Voice", "Commander")
    deck.add_category("Ramp", 8)
    deck.add_card("Sol Ring", "Ramp")
    deck.add_card("Cultivate", "Ramp")
    deck.add_category("Removal", 6)
    deck.add_card("Forest", "Basic Lands")
    deck.add_card("Forest", "Basic Lands")
    deck.add_card("Mountain", "Basic Lands")
    return deck


def _deck_no_modes() -> Decklist:
    deck = Decklist.create("NoneMode")
    deck.add_card("Atraxa, Praetors' Voice", "Commander")
    return deck


def _deck_partners() -> Decklist:
    deck = Decklist.create("Partners")
    deck.enable_partners()
    deck.add_card("Thrasios, Triton Hero", "Commander")
    deck.add_card("Tymna the Weaver", "Commander")
    return deck


def _deck_background() -> Decklist:
    deck = Decklist.create("Background")
    deck.enable_background()
    deck.add_card("Syr Armont, the Redeemer", "Commander")
    deck.add_card("Inspiring Leader", "Commander")
    return deck


def _deck_partners_and_background() -> Decklist:
    deck = Decklist.create("Both")
    deck.enable_partners()
    deck.enable_background()
    return deck


def _deck_companion() -> Decklist:
    deck = Decklist.create("Companion")
    deck.enable_companion()
    deck.add_card("Lurrus of the Dream-Den", "Companion")
    deck.add_card("Atraxa, Praetors' Voice", "Commander")
    return deck


def _deck_with_uncategorized() -> Decklist:
    deck = Decklist.create("Uncategorized")
    deck.add_category("Ramp", 2)
    deck.add_card("Sol Ring", "Ramp")
    deck.add_card("Arcane Signet", "Ramp")
    # Trigger Uncategorized creation via remove
    deck.remove_card("Sol Ring")
    return deck


# ---------------------------------------------------------------------------
# PlaintextRepository — save / load
# ---------------------------------------------------------------------------


class TestPlaintextRepositorySaveLoad:
    def test_save_creates_file(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "decklist.bak")
        deck = _full_deck()
        repo.save(deck)
        assert (tmp_path / "decklist.bak").exists()

    def test_save_creates_parent_directories(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "nested" / "dir" / "decklist.bak")
        repo.save(_deck_no_modes())
        assert (tmp_path / "nested" / "dir" / "decklist.bak").exists()

    def test_load_returns_none_when_file_missing(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "nonexistent.bak")
        assert repo.load() is None

    def test_round_trip_preserves_deck_name(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _full_deck()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert loaded.name == deck.name

    def test_round_trip_preserves_categories(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _full_deck()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        for key in deck.categories:
            assert key in loaded.categories

    def test_round_trip_preserves_card_assignments(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _full_deck()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert "Sol Ring" in loaded.categories["ramp"].cards
        assert "Cultivate" in loaded.categories["ramp"].cards
        assert "Atraxa, Praetors' Voice" in loaded.categories["commander"].cards

    def test_round_trip_preserves_basic_lands(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _full_deck()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert loaded.categories["basic lands"].filled == 3

    def test_round_trip_no_mode_flags(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _deck_no_modes()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert not loaded.partners_enabled
        assert not loaded.background_enabled
        assert not loaded.companion_enabled

    def test_round_trip_partners_mode(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _deck_partners()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert loaded.categories["commander"].filled == 2

    def test_round_trip_background_mode(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _deck_background()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert loaded.categories["commander"].filled == 2

    def test_round_trip_companion_mode(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _deck_companion()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert "companion" in loaded.categories
        assert "Lurrus of the Dream-Den" in loaded.categories["companion"].cards

    def test_round_trip_with_uncategorized(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "deck.bak")
        deck = _deck_with_uncategorized()
        repo.save(deck)
        loaded = repo.load()
        assert loaded is not None
        assert "uncategorized" in loaded.categories
        assert "Sol Ring" in loaded.categories["uncategorized"].cards


# ---------------------------------------------------------------------------
# PlaintextRepository — delete
# ---------------------------------------------------------------------------


class TestPlaintextRepositoryDelete:
    def test_delete_removes_file(self, tmp_path):
        path = tmp_path / "deck.bak"
        repo = PlaintextRepository(path)
        repo.save(_deck_no_modes())
        assert path.exists()
        repo.delete()
        assert not path.exists()

    def test_delete_is_idempotent_when_file_missing(self, tmp_path):
        repo = PlaintextRepository(tmp_path / "nonexistent.bak")
        repo.delete()  # should not raise


# ---------------------------------------------------------------------------
# PlaintextRepository — default path from XDG
# ---------------------------------------------------------------------------


class TestPlaintextRepositoryDefaultPath:
    def test_default_path_uses_xdg_state_home(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        repo = PlaintextRepository()
        repo.save(_deck_no_modes())
        assert (tmp_path / "deckslots" / "decklist.bak").exists()

    def test_default_path_falls_back_to_home(self, monkeypatch, tmp_path):
        from pathlib import Path

        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        expected = Path.home() / ".local" / "state" / "deckslots" / "decklist.bak"
        repo = PlaintextRepository()
        assert repo._path == expected


# ---------------------------------------------------------------------------
# _get_save_path (moved to storage.py)
# ---------------------------------------------------------------------------


class TestGetSavePath:
    def test_default_uses_home(self, monkeypatch):
        from pathlib import Path

        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        path = _get_save_path()
        assert path == Path.home() / ".local" / "state" / "deckslots" / "decklist.bak"

    def test_respects_xdg_state_home(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        path = _get_save_path()
        assert path == tmp_path / "deckslots" / "decklist.bak"


# ---------------------------------------------------------------------------
# _format_save_file (moved to storage.py — spot-check)
# ---------------------------------------------------------------------------


class TestFormatSaveFileInStorage:
    def test_first_line_is_name_comment(self):
        deck = Decklist.create("My Deck")
        lines = _format_save_file(deck).splitlines()
        assert lines[0] == "# My Deck"

    def test_commander_section_written(self):
        deck = _full_deck()
        content = _format_save_file(deck)
        assert "Commander\n1 Atraxa, Praetors' Voice" in content

    def test_user_defined_category_heading_includes_slot_count(self):
        deck = _full_deck()
        content = _format_save_file(deck)
        assert "Ramp [8 slots]" in content
