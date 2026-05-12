from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CardAdded:
    card: str
    category: str


@dataclass
class CardMoved:
    card: str
    from_category: str
    to_category: str


@dataclass
class CardRemoved:
    card: str
    from_category: str


@dataclass
class CardDeleted:
    card: str
    from_category: str


@dataclass
class CategoryCreated:
    name: str
    slots: int


@dataclass
class CategoryResized:
    name: str
    old_slots: int
    new_slots: int


@dataclass
class CategoryDeleted:
    name: str
    cards_displaced: int


@dataclass
class CategoryRenamed:
    old_name: str
    new_name: str


@dataclass
class DecklistRenamed:
    old_name: str
    new_name: str


@dataclass
class ModeEnabled:
    mode: str


@dataclass
class ModeDisabled:
    mode: str


@dataclass
class TemplateApplied:
    template_name: str
    cards_displaced: int


DomainEvent = (
    CardAdded
    | CardMoved
    | CardRemoved
    | CardDeleted
    | CategoryCreated
    | CategoryResized
    | CategoryDeleted
    | CategoryRenamed
    | DecklistRenamed
    | ModeEnabled
    | ModeDisabled
    | TemplateApplied
)
