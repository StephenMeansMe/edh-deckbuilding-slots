"""In-memory undo/redo stack for a single active Decklist (Phase 3.3)."""

from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass

from deckslots.models import Decklist


@dataclass
class _Snapshot:
    deck_copy: Decklist
    description: str


class UndoStack:
    """In-memory undo/redo stack using pre-mutation Decklist deepcopies.

    Usage::

        stack = UndoStack()
        stack.push(deck, "before card add")   # call BEFORE mutating
        deck.add_card(...)                     # mutate
        # Later:
        prev = stack.undo()                    # returns the pre-mutation snapshot
    """

    def __init__(self, max_depth: int = 50) -> None:
        self._max_depth = max_depth
        self._history: deque[_Snapshot] = deque(maxlen=max_depth)
        self._future: deque[_Snapshot] = deque(maxlen=max_depth)

    @property
    def max_depth(self) -> int:
        return self._max_depth

    @property
    def can_undo(self) -> bool:
        return bool(self._history)

    @property
    def can_redo(self) -> bool:
        return bool(self._future)

    def push(self, deck: Decklist, description: str) -> None:
        """Record a snapshot of *deck* BEFORE applying the next mutation."""
        self._history.append(_Snapshot(copy.deepcopy(deck), description))
        self._future.clear()

    def undo(self, current_deck: Decklist | None = None) -> Decklist | None:
        """Return the most recent pre-mutation snapshot, or None if nothing to undo.

        Pass *current_deck* (the post-mutation state) so that redo can restore it.
        When omitted the history snapshot itself is stored in the future queue.
        """
        if not self._history:
            return None
        snap = self._history.pop()
        future_copy = (
            copy.deepcopy(current_deck) if current_deck is not None else snap.deck_copy
        )
        self._future.appendleft(_Snapshot(future_copy, snap.description))
        return snap.deck_copy

    def redo(self, current_deck: Decklist | None = None) -> Decklist | None:
        """Return the next redo snapshot, or None if nothing to redo.

        Pass *current_deck* so the current state is saved to history for a
        subsequent undo.
        """
        if not self._future:
            return None
        snap = self._future.popleft()
        history_copy = (
            copy.deepcopy(current_deck) if current_deck is not None else snap.deck_copy
        )
        self._history.append(_Snapshot(history_copy, snap.description))
        return snap.deck_copy

    def reset(self) -> None:
        """Clear both history and future (e.g. after a deck switch)."""
        self._history.clear()
        self._future.clear()
