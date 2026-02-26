from __future__ import annotations

import os
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from deckslots.cli import ParsedCommand
from deckslots.models import BASIC_LAND_NAMES, Category, Decklist


def _get_save_path() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME", "")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return base / "deckslots" / "decklist.bak"


@dataclass
class Session:
    decklist: Decklist | None = None


_CARD_LINE_RE = re.compile(r"^(\d+)\s+(.+)$")
_SAVE_CAT_RE = re.compile(r"^(.+) \[(\d+) slots\]$")


def _format_save_file(decklist: Decklist) -> str:
    sections: list[str] = [f"# {decklist.name}"]
    for cat in decklist.categories.values():
        if cat.name == "Commander":
            heading = "Commander"
        elif cat.name == "Basic Lands":
            heading = "Basic Lands"
        elif cat.name == "Uncategorized":
            heading = "Uncategorized"
        else:
            heading = f"{cat.name} [{cat.total_slots} slots]"
        lines = [heading]
        for card, qty in sorted(Counter(cat.cards).items()):
            lines.append(f"{qty} {card}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


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


def _resolve_card_and_category_suffix(
    args: list[str], categories: dict
) -> tuple[str, str] | None:
    """Greedy longest-suffix match: resolve <card-name> <to-category> from args.

    Tries the longest possible suffix of args as the category name first,
    falling back to shorter suffixes. Returns (card_name, category_key) or None.
    """
    for i in range(1, len(args)):
        candidate = " ".join(args[i:]).lower()
        if candidate in categories:
            return (" ".join(args[:i]), candidate)
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


def handle_decklist_import(session: Session, cmd: ParsedCommand) -> str:
    if not cmd.args:
        return "Usage: decklist import <filepath>"
    path = cmd.args[0]
    try:
        parsed = _parse_import_file(path)
    except FileNotFoundError as e:
        return str(e)
    except (OSError, ValueError) as e:
        return str(e)

    name = os.path.splitext(os.path.basename(path))[0]
    deck = Decklist.create(name)

    if parsed.commander is not None:
        deck.add_card(parsed.commander, "Commander")

    for card in parsed.basic_lands:
        deck.add_card(card, "Basic Lands")

    # Uncapped so imported quantities are taken at face value (including
    # duplicate non-land cards). Uncapped categories also skip the singleton
    # exclusivity check, letting cards later move to capped categories freely.
    uncategorized_cat = Category(
        name="Uncategorized",
        total_slots=0,
        fixed=True,
        capped=False,
        user_addable=False,
    )
    deck.categories["uncategorized"] = uncategorized_cat

    for card in parsed.uncategorized:
        deck.add_card(card, "Uncategorized")

    session.decklist = deck

    commander_count = 1 if parsed.commander is not None else 0
    summary = (
        f"Imported '{name}': {commander_count} commander, "
        f"{len(parsed.basic_lands)} basic lands, "
        f"{len(parsed.uncategorized)} uncategorized cards."
    )
    if parsed.commander is None:
        summary += "\nWarning: no commander found in file."
    return summary


def handle_card_move(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    if len(cmd.args) < 2:
        return "Usage: card move <card-name> <to-category>"
    resolved = _resolve_card_and_category_suffix(cmd.args, session.decklist.categories)
    if resolved is None:
        return "Category not found. Usage: card move <card-name> <to-category>"
    card, target_key = resolved
    target_cat = session.decklist.categories[target_key]

    if not target_cat.user_addable:
        return f"Cannot move cards to '{target_cat.name}'. Use 'card remove' instead."
    source_key = session.decklist.find_card(card)
    if source_key is None:
        return f"Card '{card}' not found in the decklist."
    source_cat = session.decklist.categories[source_key]

    if source_key == target_key or card in target_cat.cards:
        return f"'{card}' is already in '{target_cat.name}'."
    if target_cat.is_full:
        return f"Category '{target_cat.name}' is full (no available slots)."
    if target_cat.allowed_cards is not None and card not in target_cat.allowed_cards:
        return f"'{card}' is not allowed in '{target_cat.name}'."

    source_cat.cards.remove(card)
    target_cat.cards.append(card)
    return f"Moved '{card}' from '{source_cat.name}' to '{target_cat.name}'."


def handle_card_remove(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    if not cmd.args:
        return "Usage: card remove <card-name>"
    card = " ".join(cmd.args)
    source_key = session.decklist.find_card(card)
    if source_key is None:
        return f"Card '{card}' not found in the decklist."
    if source_key == "uncategorized":
        return (
            f"'{card}' is already in Uncategorized. "
            "Use 'card delete' to permanently remove it."
        )
    source_cat = session.decklist.categories[source_key]
    if "uncategorized" not in session.decklist.categories:
        session.decklist.categories["uncategorized"] = Category(
            name="Uncategorized",
            total_slots=0,
            fixed=True,
            capped=False,
            user_addable=False,
        )
    uncategorized_cat = session.decklist.categories["uncategorized"]
    source_cat.cards.remove(card)
    uncategorized_cat.cards.append(card)
    return f"Removed '{card}' from '{source_cat.name}'. Card is now in Uncategorized."


def handle_card_delete(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return "No active decklist. Use 'decklist create <name>' first."
    if not cmd.args:
        return "Usage: card delete <card-name>"
    card = " ".join(cmd.args)
    source_key = session.decklist.find_card(card)
    if source_key is None:
        return f"Card '{card}' not found in the decklist."
    session.decklist.categories[source_key].cards.remove(card)
    return f"Deleted '{card}' from the decklist."


def handle_help() -> str:
    return "\n".join(
        [
            "Available commands:",
            "  decklist create <name>        Create a new decklist",
            "  decklist show                 Show the active decklist",
            "  decklist import <file>        Import a decklist from a text file",
            "  category create <n> <s>       Add a category with <s> slots",
            "  category list                 List all categories",
            "  card add <cat> <name>         Add a card to a category",
            "  card move <name> <cat>        Move a card to a different category",
            "  card remove <name>            Move a card to Uncategorized",
            "  card delete <name>            Permanently remove a card",
            "  help                          Show this help message",
            "  quit / exit                   Exit the program",
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
        ("decklist", "import"): lambda cmd: handle_decklist_import(session, cmd),
        ("category", "create"): lambda cmd: handle_category_create(session, cmd),
        ("category", "list"): lambda cmd: handle_category_list(session, cmd),
        ("card", "add"): lambda cmd: handle_card_add(session, cmd),
        ("card", "move"): lambda cmd: handle_card_move(session, cmd),
        ("card", "remove"): lambda cmd: handle_card_remove(session, cmd),
        ("card", "delete"): lambda cmd: handle_card_delete(session, cmd),
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
