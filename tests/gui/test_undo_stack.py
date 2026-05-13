"""Tests for UndoStack — Phase 3.3."""

from __future__ import annotations

import pytest

from deckslots.models import Decklist


# UndoStack is a plain Python class (no Qt), so no importorskip needed.
from deckslots.gui.undo_stack import UndoStack  # noqa: E402


@pytest.fixture
def deck():
    return Decklist.create("TestDeck")


class TestUndoStackPushAndUndo:
    def test_can_undo_after_push(self, deck):
        stack = UndoStack()
        stack.push(deck, "initial")
        assert stack.can_undo

    def test_undo_restores_previous_state(self, deck):
        stack = UndoStack()
        stack.push(deck, "before add")
        deck.add_category("Ramp", 10)
        assert "ramp" in deck.categories

        restored = stack.undo()
        assert restored is not None
        assert "ramp" not in restored.categories

    def test_undo_returns_none_when_empty(self, deck):
        stack = UndoStack()
        assert stack.undo() is None

    def test_cannot_undo_when_empty(self, deck):
        stack = UndoStack()
        assert not stack.can_undo

    def test_undo_removes_from_history(self, deck):
        stack = UndoStack()
        stack.push(deck, "step 1")
        stack.undo()
        assert not stack.can_undo


class TestUndoStackRedo:
    def test_can_redo_after_undo(self, deck):
        stack = UndoStack()
        stack.push(deck, "step")
        stack.undo()
        assert stack.can_redo

    def test_redo_returns_snapshot(self, deck):
        stack = UndoStack()
        stack.push(deck, "step")
        deck.add_category("Draw", 8)
        stack.undo()
        result = stack.redo()
        assert result is not None

    def test_cannot_redo_when_fresh(self, deck):
        stack = UndoStack()
        assert not stack.can_redo

    def test_new_push_clears_redo(self, deck):
        stack = UndoStack()
        stack.push(deck, "step 1")
        deck.add_category("Ramp", 5)
        stack.push(deck, "step 2")
        # undo to get something in the redo queue
        stack.undo()
        assert stack.can_redo
        # push a new action — redo should clear
        stack.push(deck, "step 3 diverge")
        assert not stack.can_redo


class TestUndoStackMaxDepth:
    def test_max_depth_limits_history(self, deck):
        stack = UndoStack(max_depth=3)
        for _ in range(5):
            stack.push(deck, "step")
        # After 5 pushes with max_depth=3, only 3 entries remain
        count = 0
        while stack.can_undo:
            stack.undo()
            count += 1
        assert count == 3

    def test_default_max_depth_is_fifty(self, deck):
        stack = UndoStack()
        assert stack.max_depth == 50


class TestUndoStackReset:
    def test_reset_clears_history_and_future(self, deck):
        stack = UndoStack()
        stack.push(deck, "step")
        stack.undo()
        stack.reset()
        assert not stack.can_undo
        assert not stack.can_redo

    def test_push_after_reset_works(self, deck):
        stack = UndoStack()
        stack.reset()
        stack.push(deck, "fresh start")
        assert stack.can_undo
