from __future__ import annotations

from dataclasses import dataclass

from deckslots.cli import ParsedCommand
from deckslots.models import Decklist


@dataclass
class Session:
    decklist: Decklist | None = None


def handle_decklist_create(session: Session, cmd: ParsedCommand) -> str:
    if not cmd.args:
        return "Usage: decklist create <name>"
    name = cmd.args[0]
    session.decklist = Decklist.create(name)
    return f"Created decklist '{name}'."


def handle_category_create(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    if len(cmd.args) < 2:
        return "Usage: category create <name> <slots>"
    name = cmd.args[0]
    try:
        slots = int(cmd.args[1])
    except ValueError:
        return f"Invalid slot count: '{cmd.args[1]}'. Must be a number."
    try:
        session.decklist.add_category(name, slots)
    except ValueError as e:
        return str(e)
    return f"Created category '{name}' with {slots} slots."
