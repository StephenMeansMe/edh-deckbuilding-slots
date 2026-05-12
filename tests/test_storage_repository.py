"""Tests for the DecklistRepository protocol and PlaintextRepository.

Phase 1.1 establishes the storage seam. PlaintextRepository wraps the
existing _format_save_file / _parse_save_file helpers and exposes them
through the multi-deck contract used by SqliteRepository.
"""

from __future__ import annotations

import pytest

from deckslots.models import CappedCategory, Decklist
from deckslots.storage import (
    DecklistRepository,
    DecklistSummary,
    PlaintextRepository,
)


def _full_deck() -> Decklist:
    deck = Decklist.create("Atraxa Stax")
    deck.add_card("Atraxa, Praetors' Voice", "Commander")
    deck.add_category("Ramp", 10)
    deck.add_card("Sol Ring", "Ramp")
    deck.add_card("Arcane Signet", "Ramp")
    deck.categories["basic lands"].cards.extend(["Plains", "Plains", "Island"])
    return deck


def _deck_partners() -> Decklist:
    deck = Decklist.create("Thrasios + Tymna")
    deck.enable_partners()
    deck.add_card("Thrasios, Triton Hero", "Commander")
    deck.add_card("Tymna the Weaver", "Commander")
    return deck


def _deck_background() -> Decklist:
    deck = Decklist.create("Faceless + Background")
    deck.enable_background()
    deck.add_card("Faceless One", "Commander")
    deck.add_card("Cultist of the Absolute", "Commander")
    return deck


def _deck_companion() -> Decklist:
    deck = Decklist.create("Lurrus Pile")
    deck.enable_companion()
    deck.add_card("Kenrith, the Returned King", "Commander")
    deck.add_card("Lurrus of the Dream-Den", "Companion")
    return deck


class TestPlaintextRepositoryContract:
    """PlaintextRepository implements the DecklistRepository protocol."""

    def test_is_a_decklist_repository(self, tmp_path):
        repo: DecklistRepository = PlaintextRepository(path=tmp_path / "deck.bak")
        assert hasattr(repo, "save")
        assert hasattr(repo, "load")
        assert hasattr(repo, "load_by_name")
        assert hasattr(repo, "list")
        assert hasattr(repo, "delete")

    def test_list_returns_empty_when_no_save_file(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        assert repo.list() == []

    def test_save_returns_int_id(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        deck_id = repo.save(_full_deck())
        assert isinstance(deck_id, int)

    def test_save_then_list_returns_one_summary(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        deck = _full_deck()
        deck_id = repo.save(deck)
        summaries = repo.list()
        assert len(summaries) == 1
        s = summaries[0]
        assert isinstance(s, DecklistSummary)
        assert s.id == deck_id
        assert s.name == "Atraxa Stax"
        assert s.total_filled == deck.total_filled

    def test_save_then_load_round_trips_full_deck(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        original = _full_deck()
        deck_id = repo.save(original)
        loaded = repo.load(deck_id)
        assert loaded.name == original.name
        assert "ramp" in loaded.categories
        assert "Sol Ring" in loaded.categories["ramp"].cards
        assert "Atraxa, Praetors' Voice" in loaded.categories["commander"].cards
        assert sorted(loaded.categories["basic lands"].cards) == [
            "Island",
            "Plains",
            "Plains",
        ]

    def test_load_raises_keyerror_when_save_missing(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "missing.bak")
        with pytest.raises(KeyError):
            repo.load(1)

    def test_load_by_name_returns_none_when_save_missing(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "missing.bak")
        assert repo.load_by_name("Anything") is None

    def test_load_by_name_returns_deck_when_name_matches(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        repo.save(_full_deck())
        loaded = repo.load_by_name("Atraxa Stax")
        assert loaded is not None
        assert loaded.name == "Atraxa Stax"

    def test_load_by_name_returns_none_when_name_differs(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        repo.save(_full_deck())
        assert repo.load_by_name("Other") is None

    def test_delete_removes_save_file(self, tmp_path):
        path = tmp_path / "deck.bak"
        repo = PlaintextRepository(path=path)
        deck_id = repo.save(_full_deck())
        repo.delete(deck_id)
        assert not path.exists()
        assert repo.list() == []

    def test_delete_is_idempotent_when_file_missing(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "missing.bak")
        repo.delete(1)  # should not raise

    def test_round_trip_preserves_partners(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        deck_id = repo.save(_deck_partners())
        loaded = repo.load(deck_id)
        commander = loaded.categories["commander"]
        assert isinstance(commander, CappedCategory)
        assert commander.total_slots == 2
        assert len(commander.cards) == 2

    def test_round_trip_preserves_background(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        deck_id = repo.save(_deck_background())
        loaded = repo.load(deck_id)
        commander = loaded.categories["commander"]
        assert isinstance(commander, CappedCategory)
        assert commander.total_slots == 2

    def test_round_trip_preserves_companion(self, tmp_path):
        repo = PlaintextRepository(path=tmp_path / "deck.bak")
        deck_id = repo.save(_deck_companion())
        loaded = repo.load(deck_id)
        assert "companion" in loaded.categories
        assert loaded.categories["companion"].cards == [
            "Lurrus of the Dream-Den"
        ]


class TestPlaintextRepositoryDefaultPath:
    def test_default_path_uses_xdg_state_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        repo = PlaintextRepository()
        deck_id = repo.save(_full_deck())
        expected = tmp_path / "deckslots" / "decklist.bak"
        assert expected.exists()
        assert repo.load(deck_id).name == "Atraxa Stax"
