"""Tests for deckslots.status — status line rendering."""

import click

from deckslots.cli.commands import Session
from deckslots.cli.status import render_status_line
from deckslots.models import Decklist


def _session_with_deck(name: str = "Test Deck") -> Session:
    session = Session()
    session.decklist = Decklist.create(name)
    return session


# ---------------------------------------------------------------------------
# No active decklist
# ---------------------------------------------------------------------------


def test_no_decklist_shows_placeholder():
    session = Session()
    result = render_status_line(session, validation_enabled=True)
    assert "No active decklist" in result


def test_no_decklist_validation_off_shows_warning():
    session = Session()
    result = render_status_line(session, validation_enabled=False)
    assert "Validation: OFF" in result


def test_no_decklist_validation_on_omits_validation_section():
    session = Session()
    result = render_status_line(session, validation_enabled=True)
    assert "Validation" not in result


# ---------------------------------------------------------------------------
# Active decklist — basic progress display
# ---------------------------------------------------------------------------


def test_shows_decklist_name():
    session = _session_with_deck("Meren of Clan Nel Toth")
    result = render_status_line(session, validation_enabled=True)
    assert "Meren of Clan Nel Toth" in result


def test_shows_slot_progress():
    session = _session_with_deck("My Deck")
    # Fresh deck: Commander (1 slot, 0 filled), Basic Lands (uncapped, 0 filled)
    # total_slots counts only CappedCategory, so = 1; total_filled = 0
    result = render_status_line(session, validation_enabled=True)
    assert "(0/1)" in result


def test_slot_progress_updates_after_card_added():
    session = _session_with_deck("My Deck")
    session.decklist.add_card("Meren of Clan Nel Toth", "Commander")
    result = render_status_line(session, validation_enabled=True)
    assert "(1/1)" in result


def test_slot_progress_counts_only_capped_categories():
    session = _session_with_deck("My Deck")
    # Basic Lands is UncappedCategory; adding to it must not affect the filled count
    session.decklist.add_card("Plains", "Basic Lands")
    result = render_status_line(session, validation_enabled=True)
    assert "(0/1)" in result  # not (1/1)


# ---------------------------------------------------------------------------
# Warning: uncategorized cards
# ---------------------------------------------------------------------------


def test_uncategorized_warning_absent_when_empty():
    session = _session_with_deck()
    result = render_status_line(session, validation_enabled=True)
    assert "Uncategorized" not in result


def test_uncategorized_warning_shown_when_cards_present():
    session = _session_with_deck()
    session.decklist.add_card("Meren of Clan Nel Toth", "Commander")
    session.decklist.remove_card("Meren of Clan Nel Toth")  # moves to Uncategorized
    result = render_status_line(session, validation_enabled=True)
    assert "Uncategorized: 1" in result


def test_uncategorized_warning_shows_correct_count():
    session = _session_with_deck()
    session.decklist.add_category("Spells", 10)
    session.decklist.add_card("Lightning Bolt", "Spells")
    session.decklist.add_card("Counterspell", "Spells")
    session.decklist.remove_card("Lightning Bolt")
    session.decklist.remove_card("Counterspell")
    result = render_status_line(session, validation_enabled=True)
    assert "Uncategorized: 2" in result


# ---------------------------------------------------------------------------
# Warning: commander overcrowded
# ---------------------------------------------------------------------------


def test_overcrowded_warning_absent_when_not_overcrowded():
    session = _session_with_deck()
    result = render_status_line(session, validation_enabled=True)
    assert "overcrowded" not in result.lower()


def test_overcrowded_warning_shown_when_commander_overcrowded():
    session = _session_with_deck()
    # Directly append two cards to the 1-slot Commander category to force the
    # overcrowded state (disable_partners evacuates cards, so cannot reach it
    # via the normal API without then moving cards back in).
    commander = session.decklist.categories["commander"]
    commander.cards.append("Meren of Clan Nel Toth")
    commander.cards.append("Tevesh Szat, Doom of Fools")
    result = render_status_line(session, validation_enabled=True)
    assert "Commander overcrowded" in result


# ---------------------------------------------------------------------------
# Warning: companion slot empty
# ---------------------------------------------------------------------------


def test_companion_empty_warning_absent_when_companion_not_enabled():
    session = _session_with_deck()
    result = render_status_line(session, validation_enabled=True)
    assert "Companion" not in result


def test_companion_empty_warning_shown_when_enabled_but_empty():
    session = _session_with_deck()
    session.decklist.enable_companion()
    result = render_status_line(session, validation_enabled=True)
    assert "Companion: empty" in result


def test_companion_empty_warning_absent_when_companion_filled():
    session = _session_with_deck()
    session.decklist.enable_companion()
    session.decklist.add_card("Lutri, the Spellchaser", "Companion")
    result = render_status_line(session, validation_enabled=True)
    assert "Companion: empty" not in result


# ---------------------------------------------------------------------------
# Validation OFF indicator
# ---------------------------------------------------------------------------


def test_validation_off_shown_when_disabled():
    session = _session_with_deck()
    result = render_status_line(session, validation_enabled=False)
    assert "Validation: OFF" in result


def test_validation_on_omits_validation_section():
    session = _session_with_deck()
    result = render_status_line(session, validation_enabled=True)
    assert "Validation" not in result


# ---------------------------------------------------------------------------
# Section separator
# ---------------------------------------------------------------------------


def test_sections_separated_by_pipe():
    session = _session_with_deck()
    session.decklist.enable_companion()  # triggers Companion: empty warning
    result = render_status_line(session, validation_enabled=False)
    # Should have both deck info and warning sections separated by " | "
    assert " | " in result


# ---------------------------------------------------------------------------
# click.style: warning text is styled (non-empty when stripped of ANSI)
# ---------------------------------------------------------------------------


def test_uncategorized_warning_uses_click_style():
    """The warning text should survive click.unstyle (i.e. is actually styled)."""
    session = _session_with_deck()
    session.decklist.add_card("Meren of Clan Nel Toth", "Commander")
    session.decklist.remove_card("Meren of Clan Nel Toth")
    result = render_status_line(session, validation_enabled=True)
    plain = click.unstyle(result)
    # The ANSI-stripped version should still contain the warning text
    assert "Uncategorized: 1" in plain
    # And the original should be longer (has ANSI codes)
    assert len(result) > len(plain)
