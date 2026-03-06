from abc import ABC, abstractmethod
from dataclasses import dataclass, field

BASIC_LAND_NAMES: frozenset[str] = frozenset(
    {
        "Plains",
        "Island",
        "Swamp",
        "Mountain",
        "Forest",
        "Wastes",
        "Snow-Covered Plains",
        "Snow-Covered Island",
        "Snow-Covered Swamp",
        "Snow-Covered Mountain",
        "Snow-Covered Forest",
        "Snow-Covered Wastes",
    }
)


class Category(ABC):
    """Abstract base class for deck categories."""

    name: str
    fixed: bool
    allowed_cards: frozenset[str] | None
    user_addable: bool
    cards: list[str]

    @property
    @abstractmethod
    def filled(self) -> int: ...

    @property
    @abstractmethod
    def is_full(self) -> bool: ...

    @property
    @abstractmethod
    def available(self) -> int | None: ...


@dataclass
class CappedCategory(Category):
    """A category with a fixed maximum slot count (1–99)."""

    name: str
    total_slots: int
    fixed: bool = False
    allowed_cards: frozenset[str] | None = None
    user_addable: bool = True
    cards: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (1 <= self.total_slots <= 99):
            raise ValueError("total_slots must be between 1 and 99")

    @property
    def filled(self) -> int:
        return len(self.cards)

    @property
    def is_full(self) -> bool:
        return len(self.cards) >= self.total_slots

    @property
    def available(self) -> int:
        return self.total_slots - len(self.cards)


@dataclass
class UncappedCategory(Category):
    """A category with no upper slot limit (basic lands, uncategorized)."""

    name: str
    fixed: bool = False
    allowed_cards: frozenset[str] | None = None
    user_addable: bool = True
    cards: list[str] = field(default_factory=list)

    @property
    def filled(self) -> int:
        return len(self.cards)

    @property
    def is_full(self) -> bool:
        return False

    @property
    def available(self) -> None:
        return None


@dataclass
class Decklist:
    name: str
    categories: dict[str, Category] = field(default_factory=dict)

    @property
    def total_slots(self) -> int:
        return sum(
            c.total_slots
            for c in self.categories.values()
            if isinstance(c, CappedCategory)
        )

    @property
    def total_filled(self) -> int:
        return sum(c.filled for c in self.categories.values())

    def add_category(self, name: str, slots: int) -> None:
        key = name.lower()
        if key in self.categories:
            raise ValueError(f"Category '{name}' already exists")
        self.categories[key] = CappedCategory(name=name, total_slots=slots)

    def add_card(self, card: str, category_name: str) -> None:
        key = category_name.lower()
        if key not in self.categories:
            raise ValueError(f"Category '{category_name}' not found.")
        cat = self.categories[key]
        if cat.allowed_cards is not None and card not in cat.allowed_cards:
            raise ValueError(f"'{card}' is not allowed in '{category_name}'.")
        if cat.is_full:
            raise ValueError(
                f"Category '{category_name}' is full (no available slots)."
            )
        if isinstance(cat, CappedCategory):
            for other in self.categories.values():
                if isinstance(other, CappedCategory) and card in other.cards:
                    raise ValueError(f"'{card}' is already in the decklist.")
        cat.cards.append(card)

    def find_card(self, card: str) -> str | None:
        """Return the category key containing this card, or None if not found."""
        for key, cat in self.categories.items():
            if card in cat.cards:
                return key
        return None

    def rename_category(self, old_name: str, new_name: str) -> None:
        old_key = old_name.lower()
        new_key = new_name.lower()
        if old_key not in self.categories:
            raise ValueError(f"Category '{old_name}' not found.")
        cat = self.categories[old_key]
        if cat.fixed:
            raise ValueError(f"Cannot rename fixed category '{cat.name}'.")
        if new_key in self.categories and new_key != old_key:
            raise ValueError(f"Category '{new_name}' already exists.")
        del self.categories[old_key]
        cat.name = new_name
        self.categories[new_key] = cat

    def rename(self, new_name: str) -> None:
        self.name = new_name

    @classmethod
    def create(cls, name: str) -> "Decklist":
        commander = CappedCategory(name="Commander", total_slots=1, fixed=True)
        basic_lands = UncappedCategory(
            name="Basic Lands",
            fixed=True,
            allowed_cards=BASIC_LAND_NAMES,
        )
        return cls(
            name=name,
            categories={"commander": commander, "basic lands": basic_lands},
        )
