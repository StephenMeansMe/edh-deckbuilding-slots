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


@dataclass
class Category:
    name: str
    total_slots: int
    fixed: bool = False
    capped: bool = True
    # Whitelist; enforced by future add_card method.
    allowed_cards: frozenset[str] | None = None
    cards: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.capped:
            if self.total_slots < 1 or self.total_slots > 99:
                raise ValueError("total_slots must be between 1 and 99")
        else:
            if self.total_slots < 0:
                raise ValueError("total_slots must not be negative")

    @property
    def filled(self) -> int:
        return len(self.cards)

    @property
    def available(self) -> int | None:
        if not self.capped:
            return None
        return self.total_slots - self.filled

    @property
    def is_full(self) -> bool:
        if not self.capped:
            return False
        return self.available == 0


@dataclass
class Decklist:
    name: str
    categories: dict[str, Category] = field(default_factory=dict)

    @property
    def total_slots(self) -> int:
        return sum(c.total_slots for c in self.categories.values())

    @property
    def total_filled(self) -> int:
        return sum(c.filled for c in self.categories.values())

    def add_category(self, name: str, slots: int) -> None:
        key = name.lower()
        if key in self.categories:
            raise ValueError(f"Category '{name}' already exists")
        self.categories[key] = Category(name=name, total_slots=slots)

    def add_card(self, card: str, category_name: str) -> None:
        key = category_name.lower()
        if key not in self.categories:
            raise ValueError(f"Category '{category_name}' not found.")
        cat = self.categories[key]
        if cat.allowed_cards is not None and card not in cat.allowed_cards:
            raise ValueError(f"'{card}' is not allowed in '{category_name}'.")
        if cat.is_full:
            raise ValueError(f"Category '{category_name}' is full (no available slots).")
        if cat.capped:
            for other in self.categories.values():
                if other.capped and card in other.cards:
                    raise ValueError(f"'{card}' is already in the decklist.")
        cat.cards.append(card)

    @classmethod
    def create(cls, name: str) -> "Decklist":
        commander = Category(name="Commander", total_slots=1, fixed=True)
        basic_lands = Category(
            name="Basic Lands",
            total_slots=0,
            fixed=True,
            capped=False,
            allowed_cards=BASIC_LAND_NAMES,
        )
        return cls(
            name=name,
            categories={"commander": commander, "basic lands": basic_lands},
        )
