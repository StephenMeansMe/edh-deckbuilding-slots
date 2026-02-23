from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from deckslots.cli import ParsedCommand
from deckslots.models import BASIC_LAND_NAMES, Decklist


@dataclass
class Session:
    decklist: Decklist | None = None


_CARD_LINE_RE = re.compile(r"^(\d+)\s+(.+)$")


@dataclass
class ParsedImport:
    commander: str | None
    basic_lands: list[str]
    uncategorized: list[str]


def _parse_import_file(path: str) -> ParsedImport:
    try:
        with open(path) as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: '{path}'")
    except OSError as e:
        raise OSError(f"Cannot read file '{path}': {e}")

    section: str | None = None
    commander: str | None = None
    basic_lands: list[str] = []
    uncategorized: list[str] = []
    any_card_found = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower() == "commander":
            section = "commander"
            continue
        if stripped.lower() == "maindeck":
            section = "maindeck"
            continue
        m = _CARD_LINE_RE.match(stripped)
        if m:
            qty = int(m.group(1))
            card = m.group(2).strip()
            any_card_found = True
            if section == "commander":
                commander = card
            elif section == "maindeck":
                if card in BASIC_LAND_NAMES:
                    basic_lands.extend([card] * qty)
                else:
                    uncategorized.extend([card] * qty)

    if not any_card_found:
        raise ValueError(f"No recognizable card lines found in '{path}'.")

    return ParsedImport(
        commander=commander,
        basic_lands=basic_lands,
        uncategorized=uncategorized,
    )


def _resolve_category_and_card(
    args: list[str], categories: dict
) -> tuple[str, str] | None:
    for i in range(len(args) - 1, 0, -1):
        candidate = " ".join(args[:i]).lower()
        if candidate in categories:
            return (candidate, " ".join(args[i:]))
    return None


def handle_decklist_create(session: Session, cmd: ParsedCommand) -> str:
    if not cmd.args:
        return "Usage: decklist create <name>"
    name = cmd.args[0]
    session.decklist = Decklist.create(name)
    return f"Created decklist '{name}'."


def handle_card_add(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    if len(cmd.args) < 2:
        return "Usage: card add <category> <card-name>"
    resolved = _resolve_category_and_card(cmd.args, session.decklist.categories)
    if resolved is None:
        return "Category not found. Usage: card add <category> <card-name>"
    category_key, card = resolved
    cat = session.decklist.categories[category_key]
    if not cat.user_addable:
        return f"Cannot add cards to '{cat.name}' directly."
    category_name = cat.name
    try:
        session.decklist.add_card(card, category_name)
    except ValueError as e:
        return str(e)
    return f"Added '{card}' to '{category_name}'."


def handle_category_create(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    if len(cmd.args) < 2:
        return "Usage: category create <name> <slots>"
    *name_parts, slots_str = cmd.args
    name = " ".join(name_parts)
    try:
        slots = int(slots_str)
    except ValueError:
        return f"Invalid slot count: '{slots_str}'. Must be a number."
    try:
        session.decklist.add_category(name, slots)
    except ValueError as e:
        return str(e)
    return f"Created category '{name}' with {slots} slots."


def _format_category_line(cat) -> str:
    if not cat.capped:
        return f"  {cat.name}: {cat.filled} slots filled (uncapped)"
    return f"  {cat.name}: {cat.filled}/{cat.total_slots} slots filled"


def handle_category_list(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    lines = ["Categories:"]
    for cat in session.decklist.categories.values():
        lines.append(_format_category_line(cat))
    return "\n".join(lines)


def handle_help() -> str:
    return "\n".join(
        [
            "Available commands:",
            "  decklist create <name>    Create a new decklist",
            "  decklist show             Show the active decklist",
            "  category create <n> <s>   Add a category with <s> slots",
            "  category list             List all categories",
            "  card add <cat> <name>     Add a card to a category",
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
        lines.append(_format_category_line(cat))
    return "\n".join(lines)


def register_all_handlers(
    session: Session,
) -> dict[tuple[str, str], Callable[[ParsedCommand], str]]:
    return {
        ("decklist", "create"): lambda cmd: handle_decklist_create(session, cmd),
        ("decklist", "show"): lambda cmd: handle_decklist_show(session, cmd),
        ("category", "create"): lambda cmd: handle_category_create(session, cmd),
        ("category", "list"): lambda cmd: handle_category_list(session, cmd),
        ("card", "add"): lambda cmd: handle_card_add(session, cmd),
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
