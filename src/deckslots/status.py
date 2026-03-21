"""Status line rendering for the deckslots REPL."""

from __future__ import annotations

import click

from deckslots.commands import Session
from deckslots.models import CappedCategory


def render_status_line(session: Session, validation_enabled: bool) -> str:
    """Return a compact one-line status string for the current session.

    Sections are joined with ' | '.  Warning indicators (uncategorized cards,
    overcrowded commander, empty companion slot, validation off) are styled
    yellow and bold via click.style().

    The filled count reflects only CappedCategory instances so that uncapped
    holding areas (Basic Lands, Uncategorized) don't inflate the number.
    """
    sections: list[str] = []

    if session.decklist is None:
        sections.append("No active decklist")
    else:
        deck = session.decklist
        capped_filled = sum(
            cat.filled
            for cat in deck.categories.values()
            if isinstance(cat, CappedCategory)
        )
        sections.append(f"{deck.name} ({capped_filled}/{deck.total_slots})")

        uncategorized = deck.categories.get("uncategorized")
        if uncategorized is not None and uncategorized.filled > 0:
            sections.append(
                click.style(f"Uncategorized: {uncategorized.filled}", fg="yellow", bold=True)
            )

        if deck.commander_overcrowded:
            sections.append(click.style("Commander overcrowded", fg="yellow", bold=True))

        if deck.companion_slot_empty:
            sections.append(click.style("Companion: empty", fg="yellow", bold=True))

    if not validation_enabled:
        sections.append(click.style("Validation: OFF", fg="yellow", bold=True))

    return " | ".join(sections)
