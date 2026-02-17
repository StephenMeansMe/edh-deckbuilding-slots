from dataclasses import dataclass, field


@dataclass
class Category:
    name: str
    total_slots: int
    fixed: bool = False
    cards: set[str] = field(default_factory=set)

    def __post_init__(self):
        if self.total_slots < 1 or self.total_slots > 99:
            raise ValueError("total_slots must be between 1 and 99")

    @property
    def filled(self) -> int:
        return len(self.cards)

    @property
    def available(self) -> int:
        return self.total_slots - self.filled

    @property
    def is_full(self) -> bool:
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

    @classmethod
    def create(cls, name: str) -> "Decklist":
        commander = Category(name="Commander", total_slots=1, fixed=True)
        return cls(name=name, categories={"commander": commander})
