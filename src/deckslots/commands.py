from __future__ import annotations

from collections.abc import Callable
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


def handle_category_list(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    lines = ["Categories:"]
    for cat in session.decklist.categories.values():
        lines.append(f"  {cat.name}: {cat.filled}/{cat.total_slots} slots filled")
    return "\n".join(lines)


def handle_help() -> str:
    return "\n".join(
        [
            "Available commands:",
            "  decklist create <name>    Create a new decklist",
            "  decklist show             Show the active decklist",
            "  category create <n> <s>   Add a category with <s> slots",
            "  category list             List all categories",
            "  help                      Show this help message",
            "  quit / exit               Exit the program",
        ]
    )


def handle_decklist_show(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    deck = session.decklist
    lines = [f"Decklist: {deck.name}"]
    lines.append(f"Total slots: {deck.total_slots} ({deck.total_filled} filled)")
    lines.append("Categories:")
    for cat in deck.categories.values():
        lines.append(f"  {cat.name}: {cat.filled}/{cat.total_slots} slots filled")
    return "\n".join(lines)


def register_all_handlers(
    session: Session,
) -> dict[tuple[str, str], Callable[[ParsedCommand], str]]:
    return {
        ("decklist", "create"): lambda cmd: handle_decklist_create(session, cmd),
        ("decklist", "show"): lambda cmd: handle_decklist_show(session, cmd),
        ("category", "create"): lambda cmd: handle_category_create(session, cmd),
        ("category", "list"): lambda cmd: handle_category_list(session, cmd),
    }


def dispatch(
    cmd: ParsedCommand,
    registry: dict[tuple[str, str], Callable[[ParsedCommand], str]],
) -> str:
    key = (cmd.obj, cmd.verb)
    handler = registry.get(key)
    if handler is None:
        return f"Unknown command: {cmd.raw}"
    return handler(cmd)
