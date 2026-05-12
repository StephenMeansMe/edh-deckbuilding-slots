"""Tests for the service layer (services.py + events.py)."""

import pytest

from deckslots.events import (
    CardAdded,
    CardDeleted,
    CardMoved,
    CardRemoved,
    CategoryCreated,
    CategoryDeleted,
    CategoryRenamed,
    CategoryResized,
    DecklistRenamed,
    ModeDisabled,
    ModeEnabled,
    TemplateApplied,
)
from deckslots.models import CappedCategory, Decklist
from deckslots.services import (
    CommandResult,
    add_card,
    apply_template,
    can_drop,
    create_category,
    delete_card,
    delete_category,
    disable_background,
    disable_companion,
    disable_partners,
    enable_background,
    enable_companion,
    enable_partners,
    move_card,
    remove_card,
    rename_category,
    rename_decklist,
    resize_category,
)


def _deck_with_category(cat_name="Ramp", slots=10) -> Decklist:
    deck = Decklist.create("TestDeck")
    deck.add_category(cat_name, slots)
    return deck


# ---------------------------------------------------------------------------
# CommandResult
# ---------------------------------------------------------------------------


class TestCommandResult:
    def test_ok_result(self):
        r = CommandResult(ok=True, message="done", warnings=[], events=[])
        assert r.ok
        assert r.message == "done"
        assert r.warnings == []
        assert r.events == []

    def test_error_result(self):
        r = CommandResult(ok=False, message="bad", warnings=[], events=[])
        assert not r.ok


# ---------------------------------------------------------------------------
# add_card
# ---------------------------------------------------------------------------


class TestAddCard:
    def test_add_card_success(self):
        deck = _deck_with_category("Ramp", 10)
        result = add_card(deck, "Sol Ring", "ramp")
        assert result.ok
        assert "Sol Ring" in result.message
        assert "Ramp" in result.message
        assert any(isinstance(e, CardAdded) for e in result.events)

    def test_add_card_event_fields(self):
        deck = _deck_with_category("Ramp", 10)
        result = add_card(deck, "Sol Ring", "ramp")
        event = next(e for e in result.events if isinstance(e, CardAdded))
        assert event.card == "Sol Ring"
        assert event.category == "Ramp"

    def test_add_card_category_full(self):
        deck = Decklist.create("Deck")
        deck.add_category("Tight", 1)
        deck.add_card("Sol Ring", "Tight")
        result = add_card(deck, "Arcane Signet", "tight")
        assert not result.ok
        assert "full" in result.message.lower()
        assert result.events == []

    def test_add_card_duplicate_in_capped_category(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = add_card(deck, "Sol Ring", "ramp")
        assert not result.ok
        assert result.events == []

    def test_add_card_category_not_found(self):
        deck = Decklist.create("Deck")
        result = add_card(deck, "Sol Ring", "nonexistent")
        assert not result.ok
        assert result.events == []

    def test_add_basic_land_to_basic_lands(self):
        deck = Decklist.create("Deck")
        result = add_card(deck, "Forest", "basic lands")
        assert result.ok
        assert any(isinstance(e, CardAdded) for e in result.events)

    def test_add_card_scryfall_warning_not_found(self):
        deck = _deck_with_category("Ramp", 10)
        # A fake index with no entry for the card produces a warning
        result = add_card(deck, "NotARealCard", "ramp", scryfall_index={})
        assert result.ok  # card is still added
        assert any("not found" in w.lower() for w in result.warnings)

    def test_add_card_scryfall_commander_illegal(self):
        deck = _deck_with_category("Ramp", 10)
        # Build a minimal index entry marking the card as not commander legal
        fake_index = {
            "notacommanderlegal": {
                "name": "NotACommanderLegal",
                "legalities": {"commander": "not_legal"},
            }
        }
        result = add_card(deck, "NotACommanderLegal", "ramp", scryfall_index=fake_index)
        assert result.ok
        assert any("not legal" in w.lower() for w in result.warnings)

    def test_add_card_no_scryfall_index_no_warnings(self):
        deck = _deck_with_category("Ramp", 10)
        result = add_card(deck, "Sol Ring", "ramp", scryfall_index=None)
        assert result.ok
        assert result.warnings == []


# ---------------------------------------------------------------------------
# move_card
# ---------------------------------------------------------------------------


class TestMoveCard:
    def test_move_card_success(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_category("Draw", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = move_card(deck, "Sol Ring", "draw")
        assert result.ok
        assert "Sol Ring" in result.message
        assert any(isinstance(e, CardMoved) for e in result.events)

    def test_move_card_event_fields(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_category("Draw", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = move_card(deck, "Sol Ring", "draw")
        event = next(e for e in result.events if isinstance(e, CardMoved))
        assert event.card == "Sol Ring"
        assert event.from_category == "Ramp"
        assert event.to_category == "Draw"

    def test_move_card_already_in_target(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = move_card(deck, "Sol Ring", "ramp")
        assert not result.ok
        assert result.events == []

    def test_move_card_not_in_deck(self):
        deck = _deck_with_category("Ramp", 10)
        result = move_card(deck, "Nonexistent Card", "ramp")
        assert not result.ok
        assert result.events == []

    def test_move_card_target_full(self):
        deck = Decklist.create("Deck")
        deck.add_category("A", 1)
        deck.add_category("B", 1)
        deck.add_card("Sol Ring", "A")
        deck.add_card("Arcane Signet", "B")
        result = move_card(deck, "Sol Ring", "b")
        assert not result.ok


# ---------------------------------------------------------------------------
# can_drop
# ---------------------------------------------------------------------------


class TestCanDrop:
    def test_can_drop_valid(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_category("Draw", 10)
        deck.add_card("Sol Ring", "Ramp")
        assert can_drop(deck, "Sol Ring", "draw") is True

    def test_can_drop_target_full(self):
        deck = Decklist.create("Deck")
        deck.add_category("A", 1)
        deck.add_category("B", 1)
        deck.add_card("Sol Ring", "A")
        deck.add_card("Arcane Signet", "B")
        assert can_drop(deck, "Sol Ring", "b") is False

    def test_can_drop_already_there(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        assert can_drop(deck, "Sol Ring", "ramp") is False

    def test_can_drop_category_not_found(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        assert can_drop(deck, "Sol Ring", "nonexistent") is False

    def test_can_drop_not_user_addable(self):
        deck = Decklist.create("Deck")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        # "uncategorized" is not user_addable
        deck.remove_card("Sol Ring")
        assert can_drop(deck, "Sol Ring", "uncategorized") is False

    def test_can_drop_allowed_cards_violation(self):
        deck = Decklist.create("Deck")
        # Basic Lands only allows basic land names
        assert can_drop(deck, "Sol Ring", "basic lands") is False

    def test_can_drop_basic_land_from_uncategorized_to_basic_lands(self):
        deck = Decklist.create("Deck")
        # Forest lands in Uncategorized after a remove; can be moved to Basic Lands
        deck.add_card("Forest", "basic lands")
        deck.remove_card("Forest")  # now in Uncategorized
        assert can_drop(deck, "Forest", "basic lands") is True


# ---------------------------------------------------------------------------
# remove_card
# ---------------------------------------------------------------------------


class TestRemoveCard:
    def test_remove_card_success(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = remove_card(deck, "Sol Ring")
        assert result.ok
        assert "Sol Ring" in result.message
        assert any(isinstance(e, CardRemoved) for e in result.events)

    def test_remove_card_event_fields(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = remove_card(deck, "Sol Ring")
        event = next(e for e in result.events if isinstance(e, CardRemoved))
        assert event.card == "Sol Ring"
        assert event.from_category == "Ramp"

    def test_remove_card_not_found(self):
        deck = _deck_with_category("Ramp", 10)
        result = remove_card(deck, "Nonexistent")
        assert not result.ok
        assert result.events == []

    def test_remove_card_already_uncategorized(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.remove_card("Sol Ring")  # now in Uncategorized
        result = remove_card(deck, "Sol Ring")
        assert not result.ok


# ---------------------------------------------------------------------------
# delete_card
# ---------------------------------------------------------------------------


class TestDeleteCard:
    def test_delete_card_success(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = delete_card(deck, "Sol Ring")
        assert result.ok
        assert "Sol Ring" in result.message
        assert any(isinstance(e, CardDeleted) for e in result.events)

    def test_delete_card_not_found(self):
        deck = _deck_with_category("Ramp", 10)
        result = delete_card(deck, "Nonexistent")
        assert not result.ok
        assert result.events == []


# ---------------------------------------------------------------------------
# create_category
# ---------------------------------------------------------------------------


class TestCreateCategory:
    def test_create_category_success(self):
        deck = Decklist.create("Deck")
        result = create_category(deck, "Ramp", 10)
        assert result.ok
        assert "Ramp" in result.message
        assert any(isinstance(e, CategoryCreated) for e in result.events)

    def test_create_category_event_fields(self):
        deck = Decklist.create("Deck")
        result = create_category(deck, "Ramp", 10)
        event = next(e for e in result.events if isinstance(e, CategoryCreated))
        assert event.name == "Ramp"
        assert event.slots == 10

    def test_create_category_duplicate(self):
        deck = _deck_with_category("Ramp", 10)
        result = create_category(deck, "Ramp", 5)
        assert not result.ok
        assert result.events == []

    def test_create_category_invalid_slots(self):
        deck = Decklist.create("Deck")
        result = create_category(deck, "Ramp", 0)
        assert not result.ok
        assert result.events == []


# ---------------------------------------------------------------------------
# resize_category
# ---------------------------------------------------------------------------


class TestResizeCategory:
    def test_resize_category_success(self):
        deck = _deck_with_category("Ramp", 10)
        result = resize_category(deck, "Ramp", 15)
        assert result.ok
        assert any(isinstance(e, CategoryResized) for e in result.events)

    def test_resize_category_event_fields(self):
        deck = _deck_with_category("Ramp", 10)
        result = resize_category(deck, "Ramp", 15)
        event = next(e for e in result.events if isinstance(e, CategoryResized))
        assert event.name == "Ramp"
        assert event.old_slots == 10
        assert event.new_slots == 15

    def test_resize_category_not_found(self):
        deck = Decklist.create("Deck")
        result = resize_category(deck, "Nonexistent", 10)
        assert not result.ok
        assert result.events == []

    def test_resize_fixed_category_rejected(self):
        deck = Decklist.create("Deck")
        result = resize_category(deck, "Commander", 5)
        assert not result.ok


# ---------------------------------------------------------------------------
# delete_category
# ---------------------------------------------------------------------------


class TestDeleteCategory:
    def test_delete_category_success(self):
        deck = _deck_with_category("Ramp", 10)
        result = delete_category(deck, "Ramp")
        assert result.ok
        assert "Ramp" in result.message
        assert any(isinstance(e, CategoryDeleted) for e in result.events)

    def test_delete_category_with_cards_reports_displaced(self):
        deck = _deck_with_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = delete_category(deck, "Ramp")
        assert result.ok
        event = next(e for e in result.events if isinstance(e, CategoryDeleted))
        assert event.cards_displaced == 1

    def test_delete_category_not_found(self):
        deck = Decklist.create("Deck")
        result = delete_category(deck, "Nonexistent")
        assert not result.ok
        assert result.events == []

    def test_delete_fixed_category_rejected(self):
        deck = Decklist.create("Deck")
        result = delete_category(deck, "Commander")
        assert not result.ok


# ---------------------------------------------------------------------------
# rename_category
# ---------------------------------------------------------------------------


class TestRenameCategory:
    def test_rename_category_success(self):
        deck = _deck_with_category("Ramp", 10)
        result = rename_category(deck, "Ramp", "Acceleration")
        assert result.ok
        assert "Ramp" in result.message
        assert "Acceleration" in result.message
        assert any(isinstance(e, CategoryRenamed) for e in result.events)

    def test_rename_category_event_fields(self):
        deck = _deck_with_category("Ramp", 10)
        result = rename_category(deck, "Ramp", "Acceleration")
        event = next(e for e in result.events if isinstance(e, CategoryRenamed))
        assert event.old_name == "Ramp"
        assert event.new_name == "Acceleration"

    def test_rename_category_not_found(self):
        deck = Decklist.create("Deck")
        result = rename_category(deck, "Nonexistent", "New")
        assert not result.ok

    def test_rename_fixed_category_rejected(self):
        deck = Decklist.create("Deck")
        result = rename_category(deck, "Commander", "Leader")
        assert not result.ok


# ---------------------------------------------------------------------------
# rename_decklist
# ---------------------------------------------------------------------------


class TestRenameDeckllist:
    def test_rename_decklist_success(self):
        deck = Decklist.create("OldName")
        result = rename_decklist(deck, "NewName")
        assert result.ok
        assert deck.name == "NewName"
        assert any(isinstance(e, DecklistRenamed) for e in result.events)

    def test_rename_decklist_event_fields(self):
        deck = Decklist.create("OldName")
        result = rename_decklist(deck, "NewName")
        event = next(e for e in result.events if isinstance(e, DecklistRenamed))
        assert event.old_name == "OldName"
        assert event.new_name == "NewName"

    def test_rename_decklist_empty_name(self):
        deck = Decklist.create("OldName")
        result = rename_decklist(deck, "")
        assert not result.ok
        assert deck.name == "OldName"


# ---------------------------------------------------------------------------
# Mode services
# ---------------------------------------------------------------------------


class TestModeServices:
    def test_enable_partners(self):
        deck = Decklist.create("Deck")
        result = enable_partners(deck)
        assert result.ok
        assert deck.partners_enabled
        assert any(
            isinstance(e, ModeEnabled) and e.mode == "partners" for e in result.events
        )

    def test_disable_partners(self):
        deck = Decklist.create("Deck")
        deck.enable_partners()
        result = disable_partners(deck)
        assert result.ok
        assert not deck.partners_enabled
        assert any(
            isinstance(e, ModeDisabled) and e.mode == "partners" for e in result.events
        )

    def test_enable_background(self):
        deck = Decklist.create("Deck")
        result = enable_background(deck)
        assert result.ok
        assert deck.background_enabled
        assert any(
            isinstance(e, ModeEnabled) and e.mode == "background" for e in result.events
        )

    def test_disable_background(self):
        deck = Decklist.create("Deck")
        deck.enable_background()
        result = disable_background(deck)
        assert result.ok
        assert not deck.background_enabled
        assert any(
            isinstance(e, ModeDisabled) and e.mode == "background" for e in result.events
        )

    def test_enable_companion(self):
        deck = Decklist.create("Deck")
        result = enable_companion(deck)
        assert result.ok
        assert deck.companion_enabled
        assert any(
            isinstance(e, ModeEnabled) and e.mode == "companion" for e in result.events
        )

    def test_disable_companion(self):
        deck = Decklist.create("Deck")
        deck.enable_companion()
        result = disable_companion(deck)
        assert result.ok
        assert not deck.companion_enabled
        assert any(
            isinstance(e, ModeDisabled) and e.mode == "companion" for e in result.events
        )

    def test_enable_partners_message_includes_slot_count(self):
        deck = Decklist.create("Deck")
        result = enable_partners(deck)
        assert "2" in result.message

    def test_disable_partners_message(self):
        deck = Decklist.create("Deck")
        deck.enable_partners()
        result = disable_partners(deck)
        assert "partners" in result.message.lower() or "disabled" in result.message.lower()


# ---------------------------------------------------------------------------
# apply_template
# ---------------------------------------------------------------------------


class TestApplyTemplate:
    def test_apply_template_success(self):
        deck = _deck_with_category("Ramp", 10)
        result = apply_template(deck, "Goldfish Fundamentals")
        assert result.ok
        assert any(isinstance(e, TemplateApplied) for e in result.events)

    def test_apply_template_not_found(self):
        deck = Decklist.create("Deck")
        result = apply_template(deck, "nonexistent-template-xyz")
        assert not result.ok
        assert result.events == []
