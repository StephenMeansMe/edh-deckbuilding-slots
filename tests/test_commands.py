from deckslots.cli import ParsedCommand
from deckslots.commands import (
    Session,
    _resolve_category_and_card,
    dispatch,
    handle_card_add,
    handle_category_create,
    handle_category_list,
    handle_decklist_create,
    handle_decklist_show,
    handle_help,
    register_all_handlers,
)


def _make_session_with_deck():
    """Create a session with an active decklist for testing."""
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


class TestResolveCategoryAndCard:
    """_resolve_category_and_card matches longest category prefix from args."""

    def _categories(self, *names):
        """Build a minimal categories dict keyed by lowercase name."""
        return {name.lower(): object() for name in names}

    def test_resolves_single_word_category(self):
        """Single-word category name is matched by first token."""
        cats = self._categories("Ramp")
        result = _resolve_category_and_card(["Ramp", "Sol", "Ring"], cats)
        assert result == ("ramp", "Sol Ring")

    def test_resolves_two_word_category(self):
        """Two-word category name is matched by first two tokens."""
        cats = self._categories("Basic Lands")
        result = _resolve_category_and_card(["Basic", "Lands", "Forest"], cats)
        assert result == ("basic lands", "Forest")

    def test_returns_none_when_no_match(self):
        """Returns None when no prefix of args matches a category key."""
        cats = self._categories("Ramp")
        result = _resolve_category_and_card(["Draw", "Sol", "Ring"], cats)
        assert result is None

    def test_prefers_longer_match_when_prefix_ambiguity(self):
        """Prefers 'Basic Lands' over 'Basic' when both exist as categories."""
        cats = self._categories("Basic", "Basic Lands")
        result = _resolve_category_and_card(["Basic", "Lands", "Forest"], cats)
        assert result == ("basic lands", "Forest")


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

    def test_category_create_handler_adds_category(self):
        """The handler adds a category to the active decklist."""
        session = _make_session_with_deck()
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
        session = _make_session_with_deck()
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
        session = _make_session_with_deck()
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

    def test_category_create_multi_word_name(self):
        """The handler accepts multi-word names; the last arg is the slot count."""
        session = _make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category create Test Category 5",
            obj="category",
            verb="create",
            args=["Test", "Category", "5"],
        )
        result = handle_category_create(session, cmd)
        assert "test category" in session.decklist.categories
        assert session.decklist.categories["test category"].total_slots == 5
        assert "Test Category" in result


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


class TestBasicLandsInOutput:
    """Basic Lands category appears in listing and show output."""

    def test_category_list_includes_basic_lands(self):
        """category list output includes Basic Lands."""
        session = _make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category list",
            obj="category",
            verb="list",
            args=[],
        )
        result = handle_category_list(session, cmd)
        assert "Basic Lands" in result

    def test_decklist_show_includes_basic_lands(self):
        """decklist show output includes Basic Lands."""
        session = _make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist show",
            obj="decklist",
            verb="show",
            args=[],
        )
        result = handle_decklist_show(session, cmd)
        assert "Basic Lands" in result


class TestUncappedCategoryDisplay:
    """Uncapped categories render with '(uncapped)' suffix instead of '/0'."""

    def test_category_list_uncapped_uses_special_format(self):
        """Uncapped categories show 'N slots filled (uncapped)' in category list."""
        session = _make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="category list",
            obj="category",
            verb="list",
            args=[],
        )
        result = handle_category_list(session, cmd)
        assert "Basic Lands: 0 slots filled (uncapped)" in result
        assert "0/0" not in result

    def test_decklist_show_uncapped_uses_special_format(self):
        """Uncapped categories show 'N slots filled (uncapped)' in decklist show."""
        session = _make_session_with_deck()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist show",
            obj="decklist",
            verb="show",
            args=[],
        )
        result = handle_decklist_show(session, cmd)
        assert "Basic Lands: 0 slots filled (uncapped)" in result
        assert "0/0" not in result


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

    def test_help_includes_card_add(self):
        """The help output includes the card add command."""
        result = handle_help()
        assert "card add" in result


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

    def test_dispatch_card_add(self):
        """Full pipeline: register, dispatch card add, verify card in decklist."""
        session = Session()
        registry = register_all_handlers(session)
        # Create decklist
        dispatch(
            ParsedCommand(kind="object_verb", raw="decklist create TestDeck",
                          obj="decklist", verb="create", args=["TestDeck"]),
            registry,
        )
        # Create category
        dispatch(
            ParsedCommand(kind="object_verb", raw="category create Ramp 10",
                          obj="category", verb="create", args=["Ramp", "10"]),
            registry,
        )
        # Add card
        cmd = ParsedCommand(
            kind="object_verb", raw="card add Ramp Sol Ring",
            obj="card", verb="add", args=["Ramp", "Sol", "Ring"]
        )
        result = dispatch(cmd, registry)
        assert "Sol Ring" in result
        assert "Sol Ring" in session.decklist.categories["ramp"].cards


def _make_cmd(raw, obj, verb, args):
    return ParsedCommand(kind="object_verb", raw=raw, obj=obj, verb=verb, args=args)


class TestCardAddHandler:
    """handle_card_add adds a card to a category in the active decklist."""

    def test_card_add_requires_decklist(self):
        """handle_card_add returns an error when no decklist is active."""
        session = Session()
        cmd = _make_cmd(
            "card add Ramp Sol Ring", "card", "add", ["Ramp", "Sol", "Ring"]
        )
        result = handle_card_add(session, cmd)
        assert "no active decklist" in result.lower()

    def test_card_add_missing_args_returns_usage(self):
        """handle_card_add returns usage when fewer than 2 args are given."""
        session = _make_session_with_deck()
        cmd = _make_cmd("card add", "card", "add", [])
        result = handle_card_add(session, cmd)
        assert "usage" in result.lower()

    def test_card_add_adds_card_to_category(self):
        """handle_card_add places the card in the named category."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        cmd = _make_cmd(
            "card add Ramp Sol Ring", "card", "add", ["Ramp", "Sol", "Ring"]
        )
        result = handle_card_add(session, cmd)
        assert "Sol Ring" in result
        assert "Ramp" in result
        assert "Sol Ring" in session.decklist.categories["ramp"].cards

    def test_card_add_returns_error_for_missing_category(self):
        """handle_card_add returns an error when the category is not found."""
        session = _make_session_with_deck()
        cmd = _make_cmd(
            "card add Draw Sol Ring", "card", "add", ["Draw", "Sol", "Ring"]
        )
        result = handle_card_add(session, cmd)
        assert "not found" in result.lower()

    def test_card_add_returns_error_for_disallowed_card(self):
        """handle_card_add returns an error when the card is not in allowed_cards."""
        session = _make_session_with_deck()
        cmd = _make_cmd(
            "card add Basic Lands Sol Ring",
            "card", "add", ["Basic", "Lands", "Sol", "Ring"]
        )
        result = handle_card_add(session, cmd)
        assert "not allowed" in result.lower()

    def test_card_add_returns_error_when_category_full(self):
        """handle_card_add returns an error when the category is full."""
        session = _make_session_with_deck()
        session.decklist.add_category("Tiny", 1)
        session.decklist.add_card("Sol Ring", "Tiny")
        cmd = _make_cmd(
            "card add Tiny Mana Crypt", "card", "add", ["Tiny", "Mana", "Crypt"]
        )
        result = handle_card_add(session, cmd)
        assert "full" in result.lower()

    def test_card_add_returns_error_for_duplicate_card(self):
        """handle_card_add returns an error when the card is already in the decklist."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_category("Draw", 10)
        session.decklist.add_card("Sol Ring", "Ramp")
        cmd = _make_cmd(
            "card add Draw Sol Ring", "card", "add", ["Draw", "Sol", "Ring"]
        )
        result = handle_card_add(session, cmd)
        assert "already in the decklist" in result.lower()

    def test_card_add_basic_land_succeeds(self):
        """handle_card_add adds a valid basic land to the Basic Lands category."""
        session = _make_session_with_deck()
        cmd = _make_cmd(
            "card add Basic Lands Forest",
            "card", "add", ["Basic", "Lands", "Forest"]
        )
        result = handle_card_add(session, cmd)
        assert "Forest" in result
        assert "Basic Lands" in result

    def test_card_add_rejects_non_user_addable_category(self):
        """handle_card_add returns an error for categories with user_addable=False."""
        from deckslots.models import Category

        session = _make_session_with_deck()
        session.decklist.categories["uncategorized"] = Category(
            name="Uncategorized",
            total_slots=0,
            fixed=True,
            capped=False,
            user_addable=False,
        )
        cmd = _make_cmd(
            "card add Uncategorized Sol Ring",
            "card",
            "add",
            ["Uncategorized", "Sol", "Ring"],
        )
        result = handle_card_add(session, cmd)
        assert "cannot add" in result.lower()
