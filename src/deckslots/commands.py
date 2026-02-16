from __future__ import annotations

from dataclasses import dataclass

from deckslots.cli import ParsedCommand
from deckslots.models import Decklist


@dataclass
class Session:
    decklist: Decklist | None = None


def handle_decklist_create(session: Session, cmd: ParsedCommand) -> str:
    name = cmd.args[0]
    session.decklist = Decklist.create(name)
    return f"Created decklist '{name}'."
