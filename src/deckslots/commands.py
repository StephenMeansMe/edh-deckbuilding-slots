from __future__ import annotations

from dataclasses import dataclass, field

from deckslots.models import Decklist


@dataclass
class Session:
    decklist: Decklist | None = None
