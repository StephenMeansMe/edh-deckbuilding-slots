"""Tests for the scryfall module: index building, card validation, cache, config."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from deckslots.scryfall import (
    ValidationResult,
    build_name_index,
    validate_card,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LIGHTNING_BOLT = {
    "name": "Lightning Bolt",
    "legalities": {"commander": "legal"},
}

SOL_RING = {
    "name": "Sol Ring",
    "legalities": {"commander": "legal"},
}

OKO = {
    "name": "Oko, Thief of Crowns",
    "legalities": {"commander": "banned"},
}

ROFELLOS = {
    "name": "Rofellos, Llanowar Emissary",
    "legalities": {"commander": "banned"},
}

NOT_LEGAL_CARD = {
    "name": "Ancestral Recall",
    "legalities": {"commander": "not_legal"},
}

DFC_CARD = {
    "name": "Delver of Secrets // Insectile Aberration",
    "legalities": {"commander": "legal"},
    "card_faces": [
        {"name": "Delver of Secrets"},
        {"name": "Insectile Aberration"},
    ],
}

SPLIT_CARD = {
    "name": "Fire // Ice",
    "legalities": {"commander": "legal"},
    "card_faces": [
        {"name": "Fire"},
        {"name": "Ice"},
    ],
}


# ---------------------------------------------------------------------------
# build_name_index
# ---------------------------------------------------------------------------


class TestBuildNameIndex:
    def test_indexes_simple_card_by_lowercase_name(self):
        index = build_name_index([LIGHTNING_BOLT])
        assert "lightning bolt" in index

    def test_indexes_multiple_cards(self):
        index = build_name_index([LIGHTNING_BOLT, SOL_RING, OKO])
        assert "lightning bolt" in index
        assert "sol ring" in index
        assert "oko, thief of crowns" in index

    def test_empty_list_returns_empty_index(self):
        assert build_name_index([]) == {}

    def test_dfc_indexed_by_full_name(self):
        index = build_name_index([DFC_CARD])
        assert "delver of secrets // insectile aberration" in index

    def test_dfc_also_indexed_by_each_face_name(self):
        index = build_name_index([DFC_CARD])
        assert "delver of secrets" in index
        assert "insectile aberration" in index

    def test_dfc_face_entries_reference_same_card_data(self):
        index = build_name_index([DFC_CARD])
        full = index["delver of secrets // insectile aberration"]
        front = index["delver of secrets"]
        assert front is full

    def test_split_card_faces_indexed(self):
        index = build_name_index([SPLIT_CARD])
        assert "fire" in index
        assert "ice" in index
        assert "fire // ice" in index


# ---------------------------------------------------------------------------
# validate_card
# ---------------------------------------------------------------------------


class TestValidateCard:
    def setup_method(self):
        self.index = build_name_index(
            [LIGHTNING_BOLT, SOL_RING, OKO, NOT_LEGAL_CARD, DFC_CARD]
        )

    def test_found_legal_card(self):
        result = validate_card("Lightning Bolt", self.index)
        assert result.found is True
        assert result.commander_legal is True

    def test_found_banned_card(self):
        result = validate_card("Oko, Thief of Crowns", self.index)
        assert result.found is True
        assert result.commander_legal is False

    def test_found_not_legal_card(self):
        result = validate_card("Ancestral Recall", self.index)
        assert result.found is True
        assert result.commander_legal is False

    def test_card_not_in_index(self):
        result = validate_card("Gibberish Cardname XXXX", self.index)
        assert result.found is False

    def test_lookup_is_case_insensitive(self):
        result = validate_card("lightning bolt", self.index)
        assert result.found is True

    def test_dfc_front_face_found(self):
        result = validate_card("Delver of Secrets", self.index)
        assert result.found is True
        assert result.commander_legal is True

    def test_dfc_full_name_found(self):
        result = validate_card(
            "Delver of Secrets // Insectile Aberration", self.index
        )
        assert result.found is True

    def test_result_carries_original_card_name(self):
        result = validate_card("Sol Ring", self.index)
        assert result.card == "Sol Ring"

    def test_not_found_result_has_false_commander_legal(self):
        result = validate_card("Not A Card", self.index)
        assert result.found is False
        assert result.commander_legal is False


# ---------------------------------------------------------------------------
# Cache layer
# ---------------------------------------------------------------------------


class TestGetCachePath:
    def test_uses_xdg_cache_home_when_set(self, tmp_path, monkeypatch):
        from deckslots.scryfall import get_cache_path

        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
        path = get_cache_path()
        assert path == tmp_path / "deckslots" / "oracle_cards.json"

    def test_defaults_to_home_cache_dir(self, monkeypatch):
        from deckslots.scryfall import get_cache_path

        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        path = get_cache_path()
        assert path == Path.home() / ".cache" / "deckslots" / "oracle_cards.json"


class TestIsCacheStale:
    def test_returns_true_when_file_does_not_exist(self, tmp_path):
        from deckslots.scryfall import is_cache_stale

        assert is_cache_stale(tmp_path / "nonexistent.json") is True

    def test_returns_false_for_fresh_file(self, tmp_path):
        from deckslots.scryfall import is_cache_stale

        cache = tmp_path / "oracle_cards.json"
        cache.write_text("[]")
        assert is_cache_stale(cache, max_age_days=7) is False

    def test_returns_true_for_old_file(self, tmp_path):
        from deckslots.scryfall import is_cache_stale

        cache = tmp_path / "oracle_cards.json"
        cache.write_text("[]")
        old_time = time.time() - 8 * 24 * 3600  # 8 days ago
        os.utime(cache, (old_time, old_time))
        assert is_cache_stale(cache, max_age_days=7) is True

    def test_exactly_on_boundary_is_stale(self, tmp_path):
        from deckslots.scryfall import is_cache_stale

        cache = tmp_path / "oracle_cards.json"
        cache.write_text("[]")
        old_time = time.time() - 7 * 24 * 3600
        os.utime(cache, (old_time, old_time))
        assert is_cache_stale(cache, max_age_days=7) is True


class TestLoadIndexFromCache:
    def test_returns_none_when_file_missing(self, tmp_path):
        from deckslots.scryfall import load_index_from_cache

        result = load_index_from_cache(tmp_path / "missing.json")
        assert result is None

    def test_returns_index_from_valid_cache(self, tmp_path):
        from deckslots.scryfall import load_index_from_cache

        cache = tmp_path / "oracle_cards.json"
        cache.write_text(json.dumps([LIGHTNING_BOLT, SOL_RING]))
        index = load_index_from_cache(cache)
        assert index is not None
        assert "lightning bolt" in index
        assert "sol ring" in index

    def test_returns_none_for_invalid_json(self, tmp_path):
        from deckslots.scryfall import load_index_from_cache

        cache = tmp_path / "oracle_cards.json"
        cache.write_text("not valid json {{{")
        result = load_index_from_cache(cache)
        assert result is None


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestConfig:
    def test_validation_enabled_by_default(self, tmp_path, monkeypatch):
        from deckslots.config import is_validation_enabled

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        assert is_validation_enabled() is True

    def test_validation_disabled_when_config_says_so(self, tmp_path, monkeypatch):
        from deckslots.config import is_validation_enabled

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "deckslots"
        config_dir.mkdir()
        (config_dir / "config.json").write_text(
            json.dumps({"validation_enabled": False})
        )
        assert is_validation_enabled() is False

    def test_validation_enabled_when_config_says_true(self, tmp_path, monkeypatch):
        from deckslots.config import is_validation_enabled

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "deckslots"
        config_dir.mkdir()
        (config_dir / "config.json").write_text(
            json.dumps({"validation_enabled": True})
        )
        assert is_validation_enabled() is True

    def test_get_config_path_uses_xdg(self, tmp_path, monkeypatch):
        from deckslots.config import get_config_path

        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        assert get_config_path() == tmp_path / "deckslots" / "config.json"
