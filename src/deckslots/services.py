from __future__ import annotations

from dataclasses import dataclass, field

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
    DomainEvent,
    ModeDisabled,
    ModeEnabled,
    TemplateApplied,
)
from deckslots.exceptions import DecklistError
from deckslots.models import BASIC_LAND_NAMES, CappedCategory, Decklist


@dataclass
class CommandResult:
    ok: bool
    message: str
    warnings: list[str] = field(default_factory=list)
    events: list[DomainEvent] = field(default_factory=list)


def add_card(
    deck: Decklist,
    card: str,
    category_key: str,
    scryfall_index: dict | None = None,
) -> CommandResult:
    key = category_key.lower()
    if key not in deck.categories:
        return CommandResult(ok=False, message=f"Category '{category_key}' not found.")
    category_name = deck.categories[key].name
    try:
        deck.add_card(card, category_name)
    except DecklistError as e:
        return CommandResult(ok=False, message=str(e))

    warnings: list[str] = []
    if scryfall_index is not None and card not in BASIC_LAND_NAMES:
        from deckslots.scryfall import validate_card

        vr = validate_card(card, scryfall_index)
        if not vr.found:
            warnings.append(f"Warning: '{card}' not found in Scryfall database.")
        elif not vr.commander_legal:
            warnings.append(f"Warning: '{card}' is not legal in Commander format.")

    return CommandResult(
        ok=True,
        message=f"Added '{card}' to '{category_name}'.",
        warnings=warnings,
        events=[CardAdded(card=card, category=category_name)],
    )


def move_card(deck: Decklist, card: str, to_category_key: str) -> CommandResult:
    source_key = deck.find_card(card)
    source_name = deck.categories[source_key].name if source_key else None
    target_key = to_category_key.lower()
    target_name = (
        deck.categories[target_key].name
        if target_key in deck.categories
        else to_category_key
    )
    try:
        deck.move_card(card, target_name)
    except DecklistError as e:
        return CommandResult(ok=False, message=str(e))
    assert source_name is not None
    return CommandResult(
        ok=True,
        message=f"Moved '{card}' from '{source_name}' to '{target_name}'.",
        events=[
            CardMoved(card=card, from_category=source_name, to_category=target_name)
        ],
    )


def can_add(deck: Decklist, card: str, to_category_key: str) -> bool:
    """Preflight: would add_card(deck, card, to_category_key) succeed?

    Like can_drop but for cards not yet in the deck (e.g. from the Omnibar).
    Does not check whether the card already exists in the deck's history.
    """
    key = to_category_key.lower()
    if key not in deck.categories:
        return False
    cat = deck.categories[key]
    if cat.is_full:
        return False
    if cat.allowed_cards is not None and card not in cat.allowed_cards:
        return False
    if isinstance(cat, CappedCategory):
        for other in deck.categories.values():
            if isinstance(other, CappedCategory) and card in other.cards:
                return False
    return True


def can_drop(deck: Decklist, card: str, to_category_key: str) -> bool:
    """Dry-run predicate: would a move of *card* to *to_category_key* succeed?"""
    target_key = to_category_key.lower()
    if target_key not in deck.categories:
        return False
    target_cat = deck.categories[target_key]
    if not target_cat.user_addable:
        return False
    if target_cat.is_full:
        return False
    if target_cat.allowed_cards is not None and card not in target_cat.allowed_cards:
        return False
    source_key = deck.find_card(card)
    if source_key == target_key:
        return False
    if isinstance(target_cat, CappedCategory):
        for key, cat in deck.categories.items():
            if (
                key != source_key
                and isinstance(cat, CappedCategory)
                and card in cat.cards
            ):
                return False
    return True


def remove_card(deck: Decklist, card: str) -> CommandResult:
    source_key = deck.find_card(card)
    if source_key is None:
        return CommandResult(
            ok=False, message=f"Card '{card}' not found in the decklist."
        )
    if source_key == "uncategorized":
        return CommandResult(
            ok=False,
            message=(
                f"'{card}' is already in Uncategorized. "
                "Use 'card delete' to permanently remove it."
            ),
        )
    source_name = deck.categories[source_key].name
    deck.remove_card(card)
    return CommandResult(
        ok=True,
        message=f"Removed '{card}' from '{source_name}'. Card is now in Uncategorized.",
        events=[CardRemoved(card=card, from_category=source_name)],
    )


def delete_card(deck: Decklist, card: str) -> CommandResult:
    source_key = deck.find_card(card)
    if source_key is None:
        return CommandResult(
            ok=False, message=f"Card '{card}' not found in the decklist."
        )
    source_name = deck.categories[source_key].name
    try:
        deck.delete_card(card)
    except DecklistError as e:
        return CommandResult(ok=False, message=str(e))
    return CommandResult(
        ok=True,
        message=f"Deleted '{card}' from the decklist.",
        events=[CardDeleted(card=card, from_category=source_name)],
    )


def create_category(deck: Decklist, name: str, slots: int) -> CommandResult:
    try:
        deck.add_category(name, slots)
    except DecklistError as e:
        return CommandResult(ok=False, message=str(e))
    return CommandResult(
        ok=True,
        message=f"Created category '{name}' with {slots} slots.",
        events=[CategoryCreated(name=name, slots=slots)],
    )


def resize_category(deck: Decklist, name: str, new_slots: int) -> CommandResult:
    key = name.lower()
    cat = deck.categories.get(key)
    old_slots = cat.total_slots if isinstance(cat, CappedCategory) else None
    try:
        deck.resize_category(name, new_slots)
    except DecklistError as e:
        return CommandResult(ok=False, message=str(e))
    return CommandResult(
        ok=True,
        message=f"Resized '{name}' to {new_slots} slots.",
        events=[
            CategoryResized(name=name, old_slots=old_slots or 0, new_slots=new_slots)
        ],
    )


def delete_category(deck: Decklist, name: str) -> CommandResult:
    key = name.lower()
    if key not in deck.categories:
        return CommandResult(ok=False, message=f"Category '{name}' not found.")
    cards_count = len(deck.categories[key].cards)
    try:
        deck.delete_category(name)
    except DecklistError as e:
        return CommandResult(ok=False, message=str(e))
    msg = (
        f"Deleted category '{name}'. {cards_count} card(s) moved to Uncategorized."
        if cards_count
        else f"Deleted category '{name}'."
    )
    return CommandResult(
        ok=True,
        message=msg,
        events=[CategoryDeleted(name=name, cards_displaced=cards_count)],
    )


def rename_category(deck: Decklist, old_name: str, new_name: str) -> CommandResult:
    if not new_name.strip():
        return CommandResult(ok=False, message="Name cannot be empty.")
    old_key = old_name.lower()
    if old_key not in deck.categories:
        return CommandResult(ok=False, message=f"Category '{old_name}' not found.")
    display_old = deck.categories[old_key].name
    try:
        deck.rename_category(old_name, new_name)
    except DecklistError as e:
        return CommandResult(ok=False, message=str(e))
    return CommandResult(
        ok=True,
        message=f"Renamed category '{display_old}' to '{new_name}'.",
        events=[CategoryRenamed(old_name=display_old, new_name=new_name)],
    )


def rename_decklist(deck: Decklist, new_name: str) -> CommandResult:
    if not new_name.strip():
        return CommandResult(ok=False, message="Name cannot be empty.")
    old_name = deck.name
    deck.rename(new_name)
    return CommandResult(
        ok=True,
        message=f"Renamed decklist to '{new_name}'.",
        events=[DecklistRenamed(old_name=old_name, new_name=new_name)],
    )


def enable_partners(deck: Decklist) -> CommandResult:
    deck.enable_partners()
    commander = deck.categories["commander"]
    assert isinstance(commander, CappedCategory)
    slots = commander.total_slots
    return CommandResult(
        ok=True,
        message=f"Partners mode enabled. The Commander category now has {slots} slots.",
        events=[ModeEnabled(mode="partners")],
    )


def disable_partners(deck: Decklist) -> CommandResult:
    deck.disable_partners()
    return CommandResult(
        ok=True,
        message="Partners mode disabled. All commanders moved to Uncategorized.",
        events=[ModeDisabled(mode="partners")],
    )


def enable_background(deck: Decklist) -> CommandResult:
    deck.enable_background()
    commander = deck.categories["commander"]
    assert isinstance(commander, CappedCategory)
    slots = commander.total_slots
    return CommandResult(
        ok=True,
        message=(
            f"Background mode enabled. The Commander category now has {slots} slots."
        ),
        events=[ModeEnabled(mode="background")],
    )


def disable_background(deck: Decklist) -> CommandResult:
    deck.disable_background()
    return CommandResult(
        ok=True,
        message="Background mode disabled. All commanders moved to Uncategorized.",
        events=[ModeDisabled(mode="background")],
    )


def enable_companion(deck: Decklist) -> CommandResult:
    deck.enable_companion()
    return CommandResult(
        ok=True,
        message=(
            "Companion slot enabled. Add a companion with"
            " 'card add Companion <card name>'."
        ),
        events=[ModeEnabled(mode="companion")],
    )


def disable_companion(deck: Decklist) -> CommandResult:
    deck.disable_companion()
    return CommandResult(
        ok=True,
        message="Companion mode disabled. All companion cards moved to Uncategorized.",
        events=[ModeDisabled(mode="companion")],
    )


def apply_template(deck: Decklist, template_name: str) -> CommandResult:
    from deckslots.templates import find_template

    template = find_template(template_name)
    if template is None:
        return CommandResult(ok=False, message=f"Template '{template_name}' not found.")
    count = deck.apply_template(template)
    deck_name = deck.name
    return CommandResult(
        ok=True,
        message=(
            f"Applied template '{template_name}' to '{deck_name}'. "
            f"{count} card(s) moved to Uncategorized."
        ),
        events=[TemplateApplied(template_name=template_name, cards_displaced=count)],
    )
