from deckslots.cli import ParsedCommand
from deckslots.commands import (
    Session,
    dispatch,
    handle_category_create,
    handle_category_list,
    handle_decklist_create,
    handle_decklist_show,
    handle_help,
    register_all_handlers,
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


class TestDecklistShowHandler:
    """handle_decklist_show returns a summary of the active decklist."""

    def test_decklist_show_returns_summary(self):
        """The handler returns the decklist name, categories, and slot counts."""
        session = Session()
        create_cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist create TestDeck",
            obj="decklist",
            verb="create",
            args=["TestDeck"],
        )
        handle_decklist_create(session, create_cmd)
        session.decklist.add_category("Ramp", 10)

        show_cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist show",
            obj="decklist",
            verb="show",
            args=[],
        )
        result = handle_decklist_show(session, show_cmd)
        assert "TestDeck" in result
        assert "Commander" in result
        assert "Ramp" in result

    def test_decklist_show_requires_decklist(self):
        """The handler returns an error when no decklist is active."""
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist show",
            obj="decklist",
            verb="show",
            args=[],
        )
        result = handle_decklist_show(session, cmd)
        assert "no active decklist" in result.lower()


class TestCategoryListHandler:
    """handle_category_list returns all categories in the active decklist."""

    def test_category_list_returns_all_categories(self):
        """The handler lists all categories with slot info."""
        session = Session()
        create_cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist create TestDeck",
            obj="decklist",
            verb="create",
            args=["TestDeck"],
        )
        handle_decklist_create(session, create_cmd)
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_category("Removal", 5)

        list_cmd = ParsedCommand(
            kind="object_verb",
            raw="category list",
            obj="category",
            verb="list",
            args=[],
        )
        result = handle_category_list(session, list_cmd)
        assert "Commander" in result
        assert "Ramp" in result
        assert "Removal" in result

    def test_category_list_requires_decklist(self):
        """The handler returns an error when no decklist is active."""
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category list",
            obj="category",
            verb="list",
            args=[],
        )
        result = handle_category_list(session, cmd)
        assert "no active decklist" in result.lower()


class TestHelpHandler:
    """handle_help returns a list of available commands."""

    def test_help_returns_command_list(self):
        """The help output lists the available commands."""
        result = handle_help()
        assert "decklist create" in result
        assert "decklist show" in result
        assert "category create" in result
        assert "category list" in result
        assert "help" in result
        assert "quit" in result


class TestDispatch:
    """dispatch routes parsed commands to the correct handler."""

    def test_dispatch_decklist_create(self):
        """Full pipeline: register, dispatch, verify session state."""
        session = Session()
        registry = register_all_handlers(session)
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist create TestDeck",
            obj="decklist",
            verb="create",
            args=["TestDeck"],
        )
        result = dispatch(cmd, registry)
        assert session.decklist is not None
        assert session.decklist.name == "TestDeck"
        assert "TestDeck" in result

    def test_dispatch_unknown_verb_returns_error(self):
        """Dispatching an unregistered object-verb returns an error."""
        session = Session()
        registry = register_all_handlers(session)
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist nope",
            obj="decklist",
            verb="nope",
            args=[],
        )
        result = dispatch(cmd, registry)
        assert "unknown command" in result.lower()
