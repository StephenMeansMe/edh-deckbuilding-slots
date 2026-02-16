from deckslots.cli import ParsedCommand
from deckslots.commands import (
    Session,
    handle_category_create,
    handle_decklist_create,
)


class TestSession:
    """Session holds the active state for a REPL session."""

    def test_session_starts_with_no_decklist(self):
        """A new session has no active decklist."""
        session = Session()
        assert session.decklist is None


class TestDecklistCreateHandler:
    """handle_decklist_create creates a new decklist on the session."""

    def test_decklist_create_handler_creates_decklist(self):
        """The handler creates a decklist and stores it on the session."""
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist create TestDeck",
            obj="decklist",
            verb="create",
            args=["TestDeck"],
        )
        result = handle_decklist_create(session, cmd)
        assert session.decklist is not None
        assert session.decklist.name == "TestDeck"
        assert "TestDeck" in result

    def test_decklist_create_requires_name(self):
        """The handler returns a usage message when no name is provided."""
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist create",
            obj="decklist",
            verb="create",
            args=[],
        )
        result = handle_decklist_create(session, cmd)
        assert session.decklist is None
        assert "usage" in result.lower()


class TestCategoryCreateHandler:
    """handle_category_create adds a category to the active decklist."""

    def _make_session_with_deck(self):
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist create TestDeck",
            obj="decklist",
            verb="create",
            args=["TestDeck"],
        )
        handle_decklist_create(session, cmd)
        return session

    def test_category_create_handler_adds_category(self):
        """The handler adds a category to the active decklist."""
        session = self._make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category create Ramp 10",
            obj="category",
            verb="create",
            args=["Ramp", "10"],
        )
        result = handle_category_create(session, cmd)
        assert "ramp" in session.decklist.categories
        assert session.decklist.categories["ramp"].total_slots == 10
        assert "Ramp" in result

    def test_category_create_requires_decklist(self):
        """The handler returns an error when no decklist is active."""
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category create Ramp 10",
            obj="category",
            verb="create",
            args=["Ramp", "10"],
        )
        result = handle_category_create(session, cmd)
        assert "no active decklist" in result.lower()

    def test_category_create_rejects_non_numeric_slots(self):
        """The handler returns an error for non-numeric slot count."""
        session = self._make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category create Ramp abc",
            obj="category",
            verb="create",
            args=["Ramp", "abc"],
        )
        result = handle_category_create(session, cmd)
        assert "invalid" in result.lower()

    def test_category_create_rejects_zero_slots_via_handler(self):
        """The handler surfaces the model validation error for 0 slots."""
        session = self._make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category create Ramp 0",
            obj="category",
            verb="create",
            args=["Ramp", "0"],
        )
        result = handle_category_create(session, cmd)
        assert "ramp" not in session.decklist.categories
        assert "1 and 99" in result
