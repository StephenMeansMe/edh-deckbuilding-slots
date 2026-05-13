from __future__ import annotations

import dataclasses
import logging
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from deckslots import services
from deckslots.cli.parser import ParsedCommand
from deckslots.exceptions import DecklistError, ParseError
from deckslots.models import (
    BASIC_LAND_NAMES,
    CappedCategory,
    Category,
    Decklist,
    UncappedCategory,
)

# Re-exported for backward compatibility with existing tests and repl.py imports.
from deckslots.storage import (  # noqa: F401
    _CARD_LINE_RE,
    DecklistRepository,
    DecklistSummary,
    PlaintextRepository,
    _format_save_file,
    _get_save_path,
    _parse_save_file,
)
from deckslots.templates import (
    Template,
    _format_template,
    _parse_template_content,
    find_template,
    load_all_templates,
    save_user_template,
)

logger = logging.getLogger("deckslots.cli.commands")

NO_ACTIVE_DECK = "No active decklist. Use 'decklist create <name>' first."


class DispatchedHandler(Protocol):
    def __call__(self, cmd: ParsedCommand) -> str: ...


@dataclass
class Session:
    decklist: Decklist | None = None
    scryfall_index: dict | None = None
    repository: DecklistRepository = dataclasses.field(
        default_factory=PlaintextRepository
    )


@dataclass
class ParsedImport:
    commander: str | None
    basic_lands: list[str]
    uncategorized: list[str]
    companion: str | None = None


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
    companion: str | None = None
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
        if stripped.lower() == "companion":
            section = "companion"
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
            elif section == "companion":
                companion = card  # only one companion allowed
            elif section == "maindeck":
                if card in BASIC_LAND_NAMES:
                    basic_lands.extend([card] * qty)
                else:
                    uncategorized.extend([card] * qty)

    if not any_card_found:
        raise ParseError(f"No recognizable card lines found in '{path}'.")

    return ParsedImport(
        commander=commander,
        basic_lands=basic_lands,
        uncategorized=uncategorized,
        companion=companion,
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


def handle_decklist_enable_companion(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    return services.enable_companion(session.decklist).message


def handle_decklist_disable_companion(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    return services.disable_companion(session.decklist).message


def handle_decklist_enable_partners(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    return services.enable_partners(session.decklist).message


def handle_decklist_enable_background(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    return services.enable_background(session.decklist).message


def handle_decklist_disable_partners(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    return services.disable_partners(session.decklist).message


def handle_decklist_disable_background(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    return services.disable_background(session.decklist).message


def handle_decklist_create(session: Session, cmd: ParsedCommand) -> str:
    if not cmd.args:
        return "Usage: decklist create <name>"
    if "--template" in cmd.args:
        idx = cmd.args.index("--template")
        name = " ".join(cmd.args[:idx]) or cmd.args[0]
        template_name = " ".join(cmd.args[idx + 1 :])
        if not template_name:
            return "Usage: decklist create <name> --template <template-name>"
        template = find_template(template_name)
        if template is None:
            return f"Template '{template_name}' not found."
        session.decklist = Decklist.create(name)
        session.decklist.apply_template(template)
        return f"Created decklist '{name}' with template '{template_name}'."
    name = cmd.args[0]
    session.decklist = Decklist.create(name)
    return f"Created decklist '{name}'."


def handle_card_add(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if len(cmd.args) < 2:
        return "Usage: card add <category> <card-name>"
    resolved = _resolve_category_and_card(cmd.args, session.decklist.categories)
    if resolved is None:
        return "Category not found. Usage: card add <category> <card-name>"
    category_key, card = resolved
    cat = session.decklist.categories[category_key]
    if not cat.user_addable:
        return f"Cannot add cards to '{cat.name}' directly."
    if card in BASIC_LAND_NAMES and cat.name != "Basic Lands":
        return "Error: Basic lands can only be added to the 'Basic Lands' category."
    result = services.add_card(
        session.decklist, card, category_key, session.scryfall_index
    )
    if not result.ok:
        return result.message
    logger.debug("Card added: %s to %s", card, cat.name)
    parts = result.warnings + [result.message]
    return "\n".join(parts)


def handle_category_create(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if len(cmd.args) < 2:
        return "Usage: category create <name> <slots>"
    *name_parts, slots_str = cmd.args
    name = " ".join(name_parts)
    try:
        slots = int(slots_str)
    except ValueError:
        return f"Invalid slot count: '{slots_str}'. Must be a number."
    return services.create_category(session.decklist, name, slots).message


def _format_category_line(cat: Category) -> str:
    if isinstance(cat, CappedCategory):
        return f"  {cat.name}: {cat.filled}/{cat.total_slots} slots filled"
    return f"  {cat.name}: {cat.filled} slots filled (uncapped)"


def handle_category_list(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    lines = ["Categories:"]
    for cat in session.decklist.categories.values():
        lines.append(_format_category_line(cat))
    return "\n".join(lines)


def handle_category_resize(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if len(cmd.args) < 2:
        return "Usage: category resize <name> <slots>"
    *name_parts, slots_str = cmd.args
    name = " ".join(name_parts)
    try:
        slots = int(slots_str)
    except ValueError:
        return f"Invalid slot count: '{slots_str}'. Must be a number."
    return services.resize_category(session.decklist, name, slots).message


def handle_category_delete(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not cmd.args:
        return "Usage: category delete <name>"
    name = " ".join(cmd.args)
    return services.delete_category(session.decklist, name).message


def handle_category_show(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not cmd.args:
        return "Usage: category show <name>"
    name = " ".join(cmd.args)
    key = name.lower()
    if key not in session.decklist.categories:
        return f"Category '{name}' not found."
    cat = session.decklist.categories[key]
    line = _format_category_line(cat).strip()
    if not cat.cards:
        return line
    lines = [line]
    for card in cat.cards:
        lines.append(f"    {card}")
    return "\n".join(lines)


def import_deck_from_file(path: str) -> Decklist:
    """Parse an external decklist file and build a Decklist.

    Raises FileNotFoundError, OSError, or ValueError on parse failures.
    The deck's name is taken from the file's stem.
    """
    parsed = _parse_import_file(path)
    name = os.path.splitext(os.path.basename(path))[0]
    deck = Decklist.create(name)

    if parsed.commander is not None:
        deck.add_card(parsed.commander, "Commander")

    if parsed.companion is not None:
        deck.enable_companion()
        deck.add_card(parsed.companion, "Companion")

    for card in parsed.basic_lands:
        deck.add_card(card, "Basic Lands")

    # Uncapped so imported quantities are taken at face value (including
    # duplicate non-land cards). Uncapped categories also skip the singleton
    # exclusivity check, letting cards later move to capped categories freely.
    uncategorized_cat = UncappedCategory(
        name="Uncategorized",
        fixed=True,
        user_addable=False,
    )
    deck.categories["uncategorized"] = uncategorized_cat

    for card in parsed.uncategorized:
        deck.add_card(card, "Uncategorized")

    return deck


def handle_decklist_import(session: Session, cmd: ParsedCommand) -> str:
    if not cmd.args:
        return "Usage: decklist import <filepath>"
    path = cmd.args[0]
    try:
        deck = import_deck_from_file(path)
    except FileNotFoundError as e:
        return str(e)
    except (OSError, ValueError) as e:
        return str(e)

    session.decklist = deck
    logger.debug("Imported deck from %s", path)

    parsed_commander = (
        deck.categories["commander"].cards[0]
        if deck.categories["commander"].cards
        else None
    )
    basic_lands = deck.categories["basic lands"].cards
    uncategorized = (
        deck.categories["uncategorized"].cards
        if "uncategorized" in deck.categories
        else []
    )
    commander_count = 1 if parsed_commander is not None else 0
    summary = (
        f"Imported '{deck.name}': {commander_count} commander, "
        f"{len(basic_lands)} basic lands, "
        f"{len(uncategorized)} uncategorized cards."
    )
    if parsed_commander is None:
        summary += "\nWarning: no commander found in file."
    return summary


def handle_card_move(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if len(cmd.args) < 2:
        return "Usage: card move <card-name> <to-category>"
    resolved = _resolve_card_and_category_suffix(cmd.args, session.decklist.categories)
    if resolved is None:
        return "Category not found. Usage: card move <card-name> <to-category>"
    card, target_key = resolved
    target_cat = session.decklist.categories[target_key]
    # UX-level policy: Uncategorized is not a valid move target (use 'card remove')
    if not target_cat.user_addable:
        return f"Cannot move cards to '{target_cat.name}'. Use 'card remove' instead."
    # UX-level policy: basic lands must stay in Basic Lands
    if card in BASIC_LAND_NAMES and target_cat.name != "Basic Lands":
        return "Error: Basic lands can only be added to the 'Basic Lands' category."
    result = services.move_card(session.decklist, card, target_key)
    if not result.ok:
        msg = result.message
        if f"'{card}' is already in '{target_cat.name}'" in msg:
            return f"'{card}' is already in '{target_cat.name}'. Nothing to do."
        if "already in the decklist" in msg:
            return f"Error: {msg.replace('in the decklist', 'in the deck')}"
        return msg
    return result.message


def handle_card_remove(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not cmd.args:
        return "Usage: card remove <card-name>"
    card = " ".join(cmd.args)
    result = services.remove_card(session.decklist, card)
    if result.ok:
        logger.debug("Card removed: %s", card)
    return result.message


def handle_card_delete(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not cmd.args:
        return "Usage: card delete <card-name>"
    card = " ".join(cmd.args)
    result = services.delete_card(session.decklist, card)
    if result.ok:
        logger.debug("Card deleted: %s", card)
    return result.message


def _format_export_file(decklist: Decklist) -> str:
    commander_cat = decklist.categories.get("commander")
    commander_lines = ["Commander"]
    if commander_cat:
        for card in commander_cat.cards:
            commander_lines.append(f"1 {card}")

    companion_cat = decklist.categories.get("companion")
    companion_lines: list[str] = []
    if companion_cat and companion_cat.cards:
        companion_lines = ["Companion"]
        for card in companion_cat.cards:
            companion_lines.append(f"1 {card}")

    maindeck_cards: Counter[str] = Counter()
    for key, cat in decklist.categories.items():
        if key in ("commander", "companion"):
            continue
        maindeck_cards.update(cat.cards)

    maindeck_lines = ["Maindeck"]
    for card, qty in sorted(maindeck_cards.items()):
        maindeck_lines.append(f"{qty} {card}")

    sections = ["\n".join(commander_lines)]
    if companion_lines:
        sections.append("\n".join(companion_lines))
    sections.append("\n".join(maindeck_lines))
    return "\n\n".join(sections) + "\n"


def handle_decklist_export(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not cmd.args:
        return "Usage: decklist export <filepath>"
    filepath = Path(" ".join(cmd.args))
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(_format_export_file(session.decklist))
    except OSError as e:
        return f"Error exporting decklist: {e}"
    logger.debug("Exported deck to %s", filepath)
    return f"Exported '{session.decklist.name}' to '{filepath}'."


def handle_decklist_load(session: Session, cmd: ParsedCommand) -> str:
    summaries = session.repository.list()
    if not summaries:
        logger.warning("Repository is empty: no decks to load.")
        return "No saved decklist found."
    try:
        deck = session.repository.load(summaries[0].id)
    except (DecklistError, OSError, KeyError) as e:
        logger.warning("Handler error: %s", e)
        return f"Error loading save file: {e}"
    if deck is None:
        logger.warning("Save file not found")
        return "No saved decklist found."
    session.decklist = deck
    logger.debug("Deck loaded via %s", type(session.repository).__name__)
    return f"Loaded '{deck.name}'."


def handle_decklist_save(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    session.repository.save(session.decklist)
    logger.debug("Deck saved via %s", type(session.repository).__name__)
    return f"Saved '{session.decklist.name}'."


def handle_decklist_list(session: Session, cmd: ParsedCommand) -> str:
    summaries = session.repository.list()
    if not summaries:
        return "No decks saved."
    lines = ["Saved decks:"]
    for s in summaries:
        # updated_at is ISO 8601; show the date portion for readability.
        date = s.updated_at[:10] if s.updated_at else "?"
        lines.append(f"  {s.id}. {s.name} — {s.total_filled} cards ({date})")
    return "\n".join(lines)


def handle_decklist_switch(session: Session, cmd: ParsedCommand) -> str:
    if not cmd.args:
        return "Usage: decklist switch <name>"
    name = " ".join(cmd.args)
    deck = session.repository.load_by_name(name)
    if deck is None:
        return f"Deck '{name}' not found."
    session.decklist = deck
    return f"Switched to '{name}'."


def handle_decklist_delete(session: Session, cmd: ParsedCommand) -> str:
    import click

    if not cmd.args:
        return "Usage: decklist delete <name>"
    name = " ".join(cmd.args)
    target = None
    for s in session.repository.list():
        if s.name == name:
            target = s
            break
    if target is None:
        return f"Deck '{name}' not found."
    if not click.confirm(f"Delete '{name}'? This cannot be undone.", default=False):
        return "Aborted."
    session.repository.delete(target.id)
    if session.decklist is not None and session.decklist.name == name:
        session.decklist = None
    return f"Deleted '{name}'."


def validate_decklist_rename(session: Session) -> str | None:
    """Returns an error string if rename is not possible, else None."""
    if session.decklist is None:
        return NO_ACTIVE_DECK
    return None


def validate_category_rename(session: Session, old_name: str) -> str | None:
    """Returns an error string if the category cannot be renamed, else None."""
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not old_name:
        return "Usage: category rename <name>"
    key = old_name.lower()
    if key not in session.decklist.categories:
        return f"Category '{old_name}' not found."
    cat = session.decklist.categories[key]
    if cat.fixed:
        return f"Cannot rename fixed category '{cat.name}'."
    return None


def handle_decklist_rename(session: Session, new_name: str) -> str:
    """Rename the active decklist. Call after validate_decklist_rename returns None."""
    assert session.decklist is not None
    return services.rename_decklist(session.decklist, new_name).message


def handle_category_rename(session: Session, old_name: str, new_name: str) -> str:
    """Rename a category. Call only after validate_category_rename returns None."""
    assert session.decklist is not None
    return services.rename_category(session.decklist, old_name, new_name).message


def handle_template_list(session: Session, cmd: ParsedCommand) -> str:
    templates = load_all_templates()
    if not templates:
        return "No templates available."
    lines = ["Templates:"]
    for t in templates:
        label = "[built-in]" if t.builtin else "[user]"
        cat_summary = ", ".join(f"{name} ({slots})" for name, slots in t.categories)
        lines.append(f"  {label} {t.name} — {cat_summary}")
    return "\n".join(lines)


def handle_template_save(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not cmd.args:
        return "Usage: template save <name>"
    name = " ".join(cmd.args)
    categories = [
        (cat.name, cat.total_slots)
        for cat in session.decklist.categories.values()
        if not cat.fixed and isinstance(cat, CappedCategory)
    ]
    template = Template(name=name, categories=categories)
    save_user_template(template)
    return f"Saved template '{name}'."


def validate_template_save(session: Session, name: str) -> str | None:
    """Return an error string if template save is not possible, else None."""
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not name.strip():
        return "Usage: template save <name>"
    return None


def handle_decklist_apply_template(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    if not cmd.args:
        return "Usage: decklist apply-template <template-name>"
    template_name = " ".join(cmd.args)
    return services.apply_template(session.decklist, template_name).message


def handle_template_export(session: Session, cmd: ParsedCommand) -> str:
    if len(cmd.args) < 2:
        return "Usage: template export <template-name> <filepath>"
    *name_parts, filepath_str = cmd.args
    template_name = " ".join(name_parts)
    template = find_template(template_name)
    if template is None:
        return f"Template '{template_name}' not found."
    filepath = Path(filepath_str)
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(_format_template(template), encoding="utf-8")
    except OSError as e:
        return f"Error exporting template: {e}"
    return f"Exported template '{template_name}' to '{filepath}'."


def handle_template_import(session: Session, cmd: ParsedCommand) -> str:
    if not cmd.args:
        return "Usage: template import <filepath>"
    filepath = " ".join(cmd.args)
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"File not found: '{filepath}'"
    except OSError as e:
        return f"Error reading file '{filepath}': {e}"
    try:
        template = _parse_template_content(content)
    except (ParseError, Exception) as e:
        return f"Error parsing template file: {e}"
    save_user_template(template)
    return f"Imported template '{template.name}'."


def handle_help() -> str:
    return "\n".join(
        [
            "Available commands:",
            "  decklist create <name>        Create a new decklist",
            "  decklist show                 Show the active decklist",
            "  decklist import <file>        Import a decklist from a text file",
            "  decklist export <file>        Export the active decklist to a text file",
            "  decklist save                 Save the active decklist",
            "  decklist load                 Load the last saved decklist",
            "  decklist list                 List all saved decks",
            "  decklist switch <name>        Switch the active deck to a saved one",
            "  decklist delete <name>        Remove a saved deck (prompts to confirm)",
            "  decklist rename               Rename the active decklist",
            "  decklist apply-template <n>   Apply a template to the active decklist",
            "  decklist enable-partners      Allow two commanders (partner mechanic)",
            "  decklist enable-background    Allow a Background co-commander",
            "  decklist disable-partners     Disable partners; move commanders out",
            "  decklist disable-background   Disable background; move commanders out",
            "  decklist enable-companion     Enable a companion (separate zone)",
            "  decklist disable-companion    Disable companion; move to Uncategorized",
            "  category create <n> <s>       Add a category with <s> slots",
            "  category list                 List all categories",
            "  category rename <name>        Rename a user-created category",
            "  category resize <name> <s>    Resize a user-created category",
            "  category delete <name>        Delete a user-created category",
            "  category show <name>          Show details of a category",
            "  card add <cat> <name>         Add a card to a category",
            "  card move <name> <cat>        Move a card to a different category",
            "  card remove <name>            Move a card to Uncategorized",
            "  card delete <name>            Permanently remove a card",
            "  template list                 List all available templates",
            "  template save <name>          Save current categories as a template",
            "  template export <n> <file>    Export a named template to a file",
            "  template import <file>        Import a template from a file",
            "  help                          Show this help message",
            "  quit / exit                   Exit the program",
        ]
    )


def handle_decklist_show(session: Session, cmd: ParsedCommand) -> str:
    if session.decklist is None:
        return NO_ACTIVE_DECK
    deck = session.decklist
    lines = [f"Decklist: {deck.name}"]
    lines.append(f"Total slots: {deck.total_slots} ({deck.total_filled} filled)")
    lines.append("Categories:")
    for cat in deck.categories.values():
        lines.append(_format_category_line(cat))
    return "\n".join(lines)


def register_all_handlers(
    session: Session,
) -> dict[tuple[str, str], DispatchedHandler]:
    return {
        ("decklist", "create"): lambda cmd: handle_decklist_create(session, cmd),
        ("decklist", "show"): lambda cmd: handle_decklist_show(session, cmd),
        ("decklist", "import"): lambda cmd: handle_decklist_import(session, cmd),
        ("decklist", "export"): lambda cmd: handle_decklist_export(session, cmd),
        ("decklist", "save"): lambda cmd: handle_decklist_save(session, cmd),
        ("decklist", "load"): lambda cmd: handle_decklist_load(session, cmd),
        ("decklist", "list"): lambda cmd: handle_decklist_list(session, cmd),
        ("decklist", "switch"): lambda cmd: handle_decklist_switch(session, cmd),
        ("decklist", "delete"): lambda cmd: handle_decklist_delete(session, cmd),
        ("decklist", "enable-partners"): lambda cmd: handle_decklist_enable_partners(
            session, cmd
        ),
        ("decklist", "enable-background"): (
            lambda cmd: handle_decklist_enable_background(session, cmd)
        ),
        ("decklist", "disable-partners"): (
            lambda cmd: handle_decklist_disable_partners(session, cmd)
        ),
        ("decklist", "disable-background"): (
            lambda cmd: handle_decklist_disable_background(session, cmd)
        ),
        ("decklist", "enable-companion"): (
            lambda cmd: handle_decklist_enable_companion(session, cmd)
        ),
        ("decklist", "disable-companion"): (
            lambda cmd: handle_decklist_disable_companion(session, cmd)
        ),
        ("category", "create"): lambda cmd: handle_category_create(session, cmd),
        ("category", "list"): lambda cmd: handle_category_list(session, cmd),
        ("category", "resize"): lambda cmd: handle_category_resize(session, cmd),
        ("category", "delete"): lambda cmd: handle_category_delete(session, cmd),
        ("category", "show"): lambda cmd: handle_category_show(session, cmd),
        ("card", "add"): lambda cmd: handle_card_add(session, cmd),
        ("card", "move"): lambda cmd: handle_card_move(session, cmd),
        ("card", "remove"): lambda cmd: handle_card_remove(session, cmd),
        ("card", "delete"): lambda cmd: handle_card_delete(session, cmd),
        ("decklist", "apply-template"): (
            lambda cmd: handle_decklist_apply_template(session, cmd)
        ),
        ("template", "list"): lambda cmd: handle_template_list(session, cmd),
        ("template", "save"): lambda cmd: handle_template_save(session, cmd),
        ("template", "export"): lambda cmd: handle_template_export(session, cmd),
        ("template", "import"): lambda cmd: handle_template_import(session, cmd),
    }


def dispatch(
    cmd: ParsedCommand,
    registry: dict[tuple[str, str], DispatchedHandler],
) -> str:
    key = (cmd.obj, cmd.verb)
    handler = registry.get(key)  # type: ignore[arg-type]
    if handler is None:
        return f"Unknown command: {cmd.raw}"
    return handler(cmd)
