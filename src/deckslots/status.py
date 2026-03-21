"""Status line rendering for the deckslots REPL."""

from __future__ import annotations

from deckslots.commands import Session


def render_status_line(session: Session, validation_enabled: bool) -> str:
    """Return a compact one-line status string for the current session.

    Sections are joined with ' | '.  Warning indicators (uncategorized cards,
    overcrowded commander, empty companion slot, validation off) are styled
    yellow and bold via click.style().
    """
    raise NotImplementedError
