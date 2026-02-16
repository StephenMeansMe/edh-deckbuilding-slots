from dataclasses import dataclass, field


@dataclass
class Category:
    name: str
    total_slots: int
    cards: set[str] = field(default_factory=set)

    @property
    def filled(self) -> int:
        return len(self.cards)

    @property
    def available(self) -> int:
        return self.total_slots - self.filled
