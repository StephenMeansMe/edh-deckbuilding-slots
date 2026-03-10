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
    partners_enabled: bool = False
    background_enabled: bool = False
    companion_enabled: bool = False

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

    def move_card(self, card: str, to_category_name: str) -> None:
        """Move card to another category. Raises ValueError on failure."""
        source_key = self.find_card(card)
        if source_key is None:
            raise ValueError(f"Card '{card}' not found in the decklist.")
        target_key = to_category_name.lower()
        if target_key not in self.categories:
            raise ValueError(f"Category '{to_category_name}' not found.")
        target_cat = self.categories[target_key]
        if source_key == target_key:
            raise ValueError(f"'{card}' is already in '{target_cat.name}'.")
        if target_cat.is_full:
            raise ValueError(
                f"Category '{target_cat.name}' is full (no available slots)."
            )
        if (
            target_cat.allowed_cards is not None
            and card not in target_cat.allowed_cards
        ):
            raise ValueError(f"'{card}' is not allowed in '{target_cat.name}'.")
        # Enforce singleton exclusivity: card must not already exist in
        # another capped category.
        if isinstance(target_cat, CappedCategory):
            for key, cat in self.categories.items():
                if (
                    key != source_key
                    and isinstance(cat, CappedCategory)
                    and card in cat.cards
                ):
                    raise ValueError(
                        f"'{card}' is already in the decklist (in '{cat.name}')."
                    )
        self.categories[source_key].cards.remove(card)
        target_cat.cards.append(card)

    def remove_card(self, card: str) -> None:
        """Move card to Uncategorized, creating it if needed.

        Raises ValueError if not found.
        """
        source_key = self.find_card(card)
        if source_key is None:
            raise ValueError(f"Card '{card}' not found in the decklist.")
        if "uncategorized" not in self.categories:
            self.categories["uncategorized"] = UncappedCategory(
                name="Uncategorized", fixed=True, user_addable=False
            )
        source_cat = self.categories[source_key]
        source_cat.cards.remove(card)
        self.categories["uncategorized"].cards.append(card)

    def delete_card(self, card: str) -> None:
        """Permanently remove a card. Raises ValueError if not found."""
        source_key = self.find_card(card)
        if source_key is None:
            raise ValueError(f"Card '{card}' not found in the decklist.")
        self.categories[source_key].cards.remove(card)

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

    def enable_companion(self) -> None:
        """Create a separate Companion zone (1 slot, does not expand Commander)."""
        if self.companion_enabled:
            return
        self.companion_enabled = True
        self.categories["companion"] = CappedCategory(
            name="Companion", total_slots=1, fixed=True
        )

    def disable_companion(self) -> None:
        """Remove the Companion zone, moving any card to Uncategorized."""
        if not self.companion_enabled:
            return
        self.companion_enabled = False
        companion = self.categories.pop("companion", None)
        if companion and companion.cards:
            if "uncategorized" not in self.categories:
                self.categories["uncategorized"] = UncappedCategory(
                    name="Uncategorized", fixed=True, user_addable=False
                )
            for card in companion.cards:
                self.categories["uncategorized"].cards.append(card)

    def enable_partners(self) -> None:
        """Allow two commanders by expanding the Commander category by 1 slot."""
        if self.partners_enabled:
            return
        self.partners_enabled = True
        commander = self.categories["commander"]
        assert isinstance(commander, CappedCategory)
        commander.total_slots += 1

    def enable_background(self) -> None:
        """Allow a Background alongside the commander, expanding Commander by 1 slot."""
        if self.background_enabled:
            return
        self.background_enabled = True
        commander = self.categories["commander"]
        assert isinstance(commander, CappedCategory)
        commander.total_slots += 1

    def disable_partners(self) -> None:
        """Disable partners mode, moving all Commander cards to Uncategorized."""
        if not self.partners_enabled:
            return
        self.partners_enabled = False
        commander = self.categories["commander"]
        assert isinstance(commander, CappedCategory)
        commander.total_slots -= 1
        self._evacuate_commander()

    def disable_background(self) -> None:
        """Disable background mode, moving all Commander cards to Uncategorized."""
        if not self.background_enabled:
            return
        self.background_enabled = False
        commander = self.categories["commander"]
        assert isinstance(commander, CappedCategory)
        commander.total_slots -= 1
        self._evacuate_commander()

    def _evacuate_commander(self) -> None:
        """Move all Commander cards to Uncategorized."""
        if "uncategorized" not in self.categories:
            self.categories["uncategorized"] = UncappedCategory(
                name="Uncategorized", fixed=True, user_addable=False
            )
        commander = self.categories["commander"]
        for card in list(commander.cards):
            commander.cards.remove(card)
            self.categories["uncategorized"].cards.append(card)

    @property
    def companion_slot_empty(self) -> bool:
        """True when companion mode is on but no companion card has been added."""
        if not self.companion_enabled:
            return False
        companion = self.categories.get("companion")
        return companion is None or companion.filled == 0

    @property
    def commander_overcrowded(self) -> bool:
        """True when Commander holds more cards than enabled modes allow."""
        commander = self.categories.get("commander")
        if commander is None:
            return False
        max_allowed = 1 + self.partners_enabled + self.background_enabled
        return len(commander.cards) > max_allowed

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
