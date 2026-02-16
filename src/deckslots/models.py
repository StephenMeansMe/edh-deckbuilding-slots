from dataclasses import dataclass, field


@dataclass
class Category:
    name: str
    total_slots: int
    cards: set[str] = field(default_factory=set)
