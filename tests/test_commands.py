import pytest

from deckslots.cli import ParsedCommand
from deckslots.commands import (
    Session,
    _format_export_file,
    _format_save_file,
    _get_save_path,
    _parse_import_file,
    _parse_save_file,
    _resolve_card_and_category_suffix,
    _resolve_category_and_card,
    dispatch,
    handle_card_add,
    handle_card_delete,
    handle_card_move,
    handle_card_remove,
    handle_category_create,
    handle_category_list,
    handle_decklist_create,
    handle_decklist_export,
    handle_decklist_import,
    handle_decklist_load,
    handle_decklist_save,
    handle_decklist_show,
    handle_help,
    register_all_handlers,
)
from deckslots.models import Category, Decklist


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


class TestResolveSuffixCategoryAndCard:
    """_resolve_card_and_category_suffix resolves category from end of args."""

    def _categories(self, *names):
        return {name.lower(): object() for name in names}

    def test_resolves_single_word_category_from_suffix(self):
        """Single-word category at end is matched; remaining args form card name."""
        cats = self._categories("Ramp")
        result = _resolve_card_and_category_suffix(["Sol", "Ring", "Ramp"], cats)
        assert result == ("Sol Ring", "ramp")

    def test_resolves_multi_word_category_from_suffix(self):
        """Multi-word category suffix is matched; remaining args form card name."""
        cats = self._categories("Basic Lands")
        result = _resolve_card_and_category_suffix(["Forest", "Basic", "Lands"], cats)
        assert result == ("Forest", "basic lands")

    def test_returns_none_when_no_suffix_matches(self):
        """Returns None when no suffix of args matches a category key."""
        cats = self._categories("Ramp")
        result = _resolve_card_and_category_suffix(["Sol", "Ring", "Draw"], cats)
        assert result is None

    def test_prefers_longer_suffix_match(self):
        """Prefers 'Big Ramp' over 'Ramp' when both are valid category suffixes."""
        cats = self._categories("Ramp", "Big Ramp")
        result = _resolve_card_and_category_suffix(["Sol", "Ring", "Big", "Ramp"], cats)
        assert result == ("Sol Ring", "big ramp")

    def test_returns_none_for_single_element_args(self):
        """Returns None when args has only one element (no card name possible)."""
        cats = self._categories("Ramp")
        result = _resolve_card_and_category_suffix(["Ramp"], cats)
        assert result is None


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


class TestParseImportFile:
    """_parse_import_file parses the $QUANTITY $CARDNAME import format."""

    def test_parse_finds_commander(self, tmp_path):
        """Commander-section card is returned as commander."""
        f = tmp_path / "deck.txt"
        f.write_text("Commander\n1 Atraxa, Praetors' Voice\n")
        result = _parse_import_file(str(f))
        assert result.commander == "Atraxa, Praetors' Voice"

    def test_parse_routes_basic_lands(self, tmp_path):
        """Basic land names in Maindeck go to basic_lands, one entry per copy."""
        f = tmp_path / "deck.txt"
        f.write_text("Maindeck\n4 Forest\n2 Island\n")
        result = _parse_import_file(str(f))
        assert result.basic_lands == ["Forest"] * 4 + ["Island"] * 2
        assert result.uncategorized == []

    def test_parse_routes_non_land_to_uncategorized(self, tmp_path):
        """Non-basic-land Maindeck cards go to uncategorized, one entry per copy."""
        f = tmp_path / "deck.txt"
        f.write_text("Maindeck\n1 Sol Ring\n2 Arcane Signet\n")
        result = _parse_import_file(str(f))
        assert result.uncategorized == [
            "Sol Ring",
            "Arcane Signet",
            "Arcane Signet",
        ]
        assert result.basic_lands == []

    def test_parse_raises_for_missing_file(self, tmp_path):
        """FileNotFoundError is raised when the path does not exist."""
        with pytest.raises(FileNotFoundError):
            _parse_import_file(str(tmp_path / "nonexistent.txt"))

    def test_parse_raises_for_no_card_lines(self, tmp_path):
        """ValueError is raised when the file has no recognisable card lines."""
        f = tmp_path / "deck.txt"
        f.write_text("Commander\n\nMaindeck\n\n")
        with pytest.raises(ValueError, match="No recognizable card lines"):
            _parse_import_file(str(f))

    def test_parse_commander_absent_returns_none(self, tmp_path):
        """When no Commander section is present, commander is None."""
        f = tmp_path / "deck.txt"
        f.write_text("Maindeck\n1 Sol Ring\n")
        result = _parse_import_file(str(f))
        assert result.commander is None

    def test_parse_section_headings_are_case_insensitive(self, tmp_path):
        """COMMANDER and MAINDECK headings are recognised regardless of case."""
        f = tmp_path / "deck.txt"
        f.write_text("COMMANDER\n1 Atraxa\n\nMAINDECK\n1 Sol Ring\n")
        result = _parse_import_file(str(f))
        assert result.commander == "Atraxa"
        assert result.uncategorized == ["Sol Ring"]

    def test_parse_blank_lines_silently_skipped(self, tmp_path):
        """Blank lines between card entries do not cause errors."""
        f = tmp_path / "deck.txt"
        f.write_text("Commander\n\n1 Atraxa\n\nMaindeck\n\n1 Sol Ring\n\n4 Forest\n")
        result = _parse_import_file(str(f))
        assert result.commander == "Atraxa"
        assert result.uncategorized == ["Sol Ring"]
        assert result.basic_lands == ["Forest"] * 4


class TestDecklistImportHandler:
    """handle_decklist_import reads a file and builds a Decklist."""

    def test_import_creates_decklist_named_after_file(self, tmp_path):
        """Decklist name is the filename stem (no extension)."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw=f"decklist import {f}",
            obj="decklist",
            verb="import",
            args=[str(f)],
        )
        handle_decklist_import(session, cmd)
        assert session.decklist is not None
        assert session.decklist.name == "MyDeck"

    def test_import_routes_commander(self, tmp_path):
        """Commander card is placed in the Commander category."""
        f = tmp_path / "deck.txt"
        f.write_text(
            "Commander\n1 Atraxa, Praetors' Voice\n\nMaindeck\n1 Sol Ring\n"
        )
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw=f"decklist import {f}",
            obj="decklist",
            verb="import",
            args=[str(f)],
        )
        handle_decklist_import(session, cmd)
        assert "Atraxa, Praetors' Voice" in (
            session.decklist.categories["commander"].cards
        )

    def test_import_routes_basic_lands(self, tmp_path):
        """Basic land names are placed in the Basic Lands category."""
        f = tmp_path / "deck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n4 Forest\n2 Island\n")
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw=f"decklist import {f}",
            obj="decklist",
            verb="import",
            args=[str(f)],
        )
        handle_decklist_import(session, cmd)
        assert session.decklist.categories["basic lands"].filled == 6

    def test_import_creates_uncategorized_category(self, tmp_path):
        """Non-basic-land Maindeck cards go into an Uncategorized category."""
        f = tmp_path / "deck.txt"
        f.write_text(
            "Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n2 Arcane Signet\n"
        )
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw=f"decklist import {f}",
            obj="decklist",
            verb="import",
            args=[str(f)],
        )
        handle_decklist_import(session, cmd)
        cat = session.decklist.categories["uncategorized"]
        assert cat.filled == 3
        assert not cat.user_addable

    def test_import_returns_summary_string(self, tmp_path):
        """A successful import returns a human-readable summary."""
        f = tmp_path / "MyDeck.txt"
        f.write_text(
            "Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n4 Forest\n"
        )
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw=f"decklist import {f}",
            obj="decklist",
            verb="import",
            args=[str(f)],
        )
        result = handle_decklist_import(session, cmd)
        assert "MyDeck" in result
        assert "1 commander" in result
        assert "4 basic lands" in result
        assert "1 uncategorized" in result

    def test_import_returns_error_for_missing_file(self, tmp_path):
        """Returns an error string (not exception) when the file doesn't exist."""
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist import /no/such/file.txt",
            obj="decklist",
            verb="import",
            args=["/no/such/file.txt"],
        )
        result = handle_decklist_import(session, cmd)
        assert "not found" in result.lower()
        assert session.decklist is None

    def test_import_requires_filepath_arg(self):
        """Returns a usage message when no filepath is given."""
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw="decklist import",
            obj="decklist",
            verb="import",
            args=[],
        )
        result = handle_decklist_import(session, cmd)
        assert "usage" in result.lower()

    def test_import_replaces_existing_decklist(self, tmp_path):
        """An existing active decklist is silently replaced on import."""
        f = tmp_path / "NewDeck.txt"
        f.write_text("Maindeck\n1 Sol Ring\n")
        session = _make_session_with_deck()  # sets session.decklist to "TestDeck"
        cmd = ParsedCommand(
            kind="object_verb",
            raw=f"decklist import {f}",
            obj="decklist",
            verb="import",
            args=[str(f)],
        )
        handle_decklist_import(session, cmd)
        assert session.decklist.name == "NewDeck"

    def test_import_notes_missing_commander_in_summary(self, tmp_path):
        """Summary warns when no Commander section was found."""
        f = tmp_path / "deck.txt"
        f.write_text("Maindeck\n1 Sol Ring\n")
        session = Session()
        cmd = ParsedCommand(
            kind="object_verb",
            raw=f"decklist import {f}",
            obj="decklist",
            verb="import",
            args=[str(f)],
        )
        result = handle_decklist_import(session, cmd)
        assert "0 commander" in result
        assert "no commander" in result.lower()


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

    def test_help_includes_decklist_import(self):
        """The help output includes the decklist import command."""
        result = handle_help()
        assert "decklist import" in result

    def test_help_includes_card_move(self):
        """The help output includes the card move command."""
        result = handle_help()
        assert "card move" in result

    def test_help_includes_card_remove(self):
        """The help output includes the card remove command."""
        result = handle_help()
        assert "card remove" in result

    def test_help_includes_card_delete(self):
        """The help output includes the card delete command."""
        result = handle_help()
        assert "card delete" in result

    def test_help_includes_decklist_save(self):
        """The help output includes the decklist save command."""
        result = handle_help()
        assert "decklist save" in result

    def test_help_includes_decklist_load(self):
        """The help output includes the decklist load command."""
        result = handle_help()
        assert "decklist load" in result


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

    def test_dispatch_card_move(self):
        """Full pipeline: register, dispatch card move, verify card relocated."""
        session = Session()
        registry = register_all_handlers(session)
        dispatch(_make_cmd("decklist create D", "decklist", "create", ["D"]), registry)
        dispatch(
            _make_cmd("category create Ramp 10", "category", "create", ["Ramp", "10"]),
            registry,
        )
        dispatch(
            _make_cmd("category create Draw 10", "category", "create", ["Draw", "10"]),
            registry,
        )
        dispatch(
            _make_cmd("card add Ramp Sol Ring", "card", "add", ["Ramp", "Sol", "Ring"]),
            registry,
        )
        result = dispatch(
            _make_cmd(
                "card move Sol Ring Draw", "card", "move", ["Sol", "Ring", "Draw"]
            ),
            registry,
        )
        assert "Sol Ring" in result
        assert "Sol Ring" in session.decklist.categories["draw"].cards
        assert "Sol Ring" not in session.decklist.categories["ramp"].cards

    def test_dispatch_card_remove(self):
        """Full pipeline: dispatch card remove; verify card lands in Uncategorized."""
        session = Session()
        registry = register_all_handlers(session)
        dispatch(_make_cmd("decklist create D", "decklist", "create", ["D"]), registry)
        dispatch(
            _make_cmd("category create Ramp 10", "category", "create", ["Ramp", "10"]),
            registry,
        )
        dispatch(
            _make_cmd("card add Ramp Sol Ring", "card", "add", ["Ramp", "Sol", "Ring"]),
            registry,
        )
        result = dispatch(
            _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"]),
            registry,
        )
        assert "Uncategorized" in result
        assert "Sol Ring" in session.decklist.categories["uncategorized"].cards

    def test_dispatch_card_delete(self):
        """Full pipeline: register, dispatch card delete, verify card gone."""
        session = Session()
        registry = register_all_handlers(session)
        dispatch(_make_cmd("decklist create D", "decklist", "create", ["D"]), registry)
        dispatch(
            _make_cmd("category create Ramp 10", "category", "create", ["Ramp", "10"]),
            registry,
        )
        dispatch(
            _make_cmd("card add Ramp Sol Ring", "card", "add", ["Ramp", "Sol", "Ring"]),
            registry,
        )
        result = dispatch(
            _make_cmd("card delete Sol Ring", "card", "delete", ["Sol", "Ring"]),
            registry,
        )
        assert "Sol Ring" in result
        assert "Sol Ring" not in session.decklist.categories["ramp"].cards

    def test_dispatch_card_add(self):
        """Full pipeline: register, dispatch card add, verify card in decklist."""
        session = Session()
        registry = register_all_handlers(session)
        # Create decklist
        dispatch(
            ParsedCommand(
                kind="object_verb",
                raw="decklist create TestDeck",
                obj="decklist",
                verb="create",
                args=["TestDeck"],
            ),
            registry,
        )
        # Create category
        dispatch(
            ParsedCommand(
                kind="object_verb",
                raw="category create Ramp 10",
                obj="category",
                verb="create",
                args=["Ramp", "10"],
            ),
            registry,
        )
        # Add card
        cmd = ParsedCommand(
            kind="object_verb",
            raw="card add Ramp Sol Ring",
            obj="card",
            verb="add",
            args=["Ramp", "Sol", "Ring"],
        )
        result = dispatch(cmd, registry)
        assert "Sol Ring" in result
        assert "Sol Ring" in session.decklist.categories["ramp"].cards


def _make_cmd(raw, obj, verb, args):
    return ParsedCommand(kind="object_verb", raw=raw, obj=obj, verb=verb, args=args)


def _make_session_with_card_in_category(category_name, card_name, slots=10):
    """Create a session with an active decklist and a card in a named category."""
    session = _make_session_with_deck()
    session.decklist.add_category(category_name, slots)
    session.decklist.add_card(card_name, category_name)
    return session


def _add_uncategorized(session, *cards):
    """Add an Uncategorized category to the session's decklist and populate it."""
    session.decklist.categories["uncategorized"] = Category(
        name="Uncategorized",
        total_slots=0,
        fixed=True,
        capped=False,
        user_addable=False,
    )
    for card in cards:
        session.decklist.add_card(card, "Uncategorized")
    return session


class TestCardMoveHandler:
    """handle_card_move moves a card from one category to another."""

    def test_card_move_requires_decklist(self):
        """Returns an error when no decklist is active."""
        session = Session()
        cmd = _make_cmd(
            "card move Sol Ring Ramp", "card", "move", ["Sol", "Ring", "Ramp"]
        )
        result = handle_card_move(session, cmd)
        assert "no active decklist" in result.lower()

    def test_card_move_returns_error_when_card_not_in_decklist(self):
        """Returns an error when the named card is not in the decklist."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        cmd = _make_cmd(
            "card move Sol Ring Ramp", "card", "move", ["Sol", "Ring", "Ramp"]
        )
        result = handle_card_move(session, cmd)
        assert "not found" in result.lower()

    def test_card_move_returns_error_when_target_category_not_found(self):
        """Returns an error when the target category does not exist."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        cmd = _make_cmd(
            "card move Sol Ring Draw", "card", "move", ["Sol", "Ring", "Draw"]
        )
        result = handle_card_move(session, cmd)
        assert "not found" in result.lower()

    def test_card_move_returns_error_when_target_is_full(self):
        """Returns an error when the target category is capped and has no free slots."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_category("Tiny", 1)
        session.decklist.add_card("Sol Ring", "Ramp")
        session.decklist.add_card("Mana Crypt", "Tiny")
        cmd = _make_cmd(
            "card move Sol Ring Tiny", "card", "move", ["Sol", "Ring", "Tiny"]
        )
        result = handle_card_move(session, cmd)
        assert "full" in result.lower()

    def test_card_move_returns_error_when_target_is_uncategorized(self):
        """Returns an error when the target category is Uncategorized."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        _add_uncategorized(session)
        cmd = _make_cmd(
            "card move Sol Ring Uncategorized",
            "card",
            "move",
            ["Sol", "Ring", "Uncategorized"],
        )
        result = handle_card_move(session, cmd)
        assert "card remove" in result.lower()

    def test_card_move_is_noop_when_card_already_in_target(self):
        """Moving a card to the category it is already in is a silent no-op."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        cmd = _make_cmd(
            "card move Sol Ring Ramp", "card", "move", ["Sol", "Ring", "Ramp"]
        )
        result = handle_card_move(session, cmd)
        assert result == "'Sol Ring' is already in 'Ramp'. Nothing to do."

    def test_card_move_succeeds_from_uncategorized_to_capped(self):
        """Successfully moves a card from Uncategorized to a capped category."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        _add_uncategorized(session, "Sol Ring")
        cmd = _make_cmd(
            "card move Sol Ring Ramp", "card", "move", ["Sol", "Ring", "Ramp"]
        )
        result = handle_card_move(session, cmd)
        assert "Sol Ring" in result
        assert "Ramp" in result
        assert "Sol Ring" in session.decklist.categories["ramp"].cards
        assert "Sol Ring" not in session.decklist.categories["uncategorized"].cards

    def test_card_move_prints_success_message(self):
        """On success prints: Moved '<card>' from '<from>' to '<to>'."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_category("Draw", 10)
        session.decklist.add_card("Sol Ring", "Ramp")
        cmd = _make_cmd(
            "card move Sol Ring Draw", "card", "move", ["Sol", "Ring", "Draw"]
        )
        result = handle_card_move(session, cmd)
        assert result == "Moved 'Sol Ring' from 'Ramp' to 'Draw'."

    def test_card_move_removes_card_from_source_category(self):
        """After a move the source category no longer contains the card."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_category("Draw", 10)
        session.decklist.add_card("Sol Ring", "Ramp")
        cmd = _make_cmd(
            "card move Sol Ring Draw", "card", "move", ["Sol", "Ring", "Draw"]
        )
        handle_card_move(session, cmd)
        assert "Sol Ring" not in session.decklist.categories["ramp"].cards

    def test_card_move_supports_multi_word_card_name(self):
        """Greedy suffix matching correctly parses multi-word card names."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_card("Atraxa, Praetors' Voice", "Commander")
        cmd = _make_cmd(
            "card move Atraxa, Praetors' Voice Ramp",
            "card",
            "move",
            ["Atraxa,", "Praetors'", "Voice", "Ramp"],
        )
        result = handle_card_move(session, cmd)
        assert "Atraxa, Praetors' Voice" in result
        assert "Ramp" in result

    def test_card_move_rejects_disallowed_card_for_target(self):
        """Returns an error when the card is not in the target's allowed_cards."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_card("Sol Ring", "Ramp")
        cmd = _make_cmd(
            "card move Sol Ring Basic Lands",
            "card",
            "move",
            ["Sol", "Ring", "Basic", "Lands"],
        )
        result = handle_card_move(session, cmd)
        assert "not allowed" in result.lower()

    def test_card_move_rejects_when_card_already_in_another_capped_category(self):
        """card move is rejected when the card exists in a capped category other than the source."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_category("Draw", 10)
        session.decklist.add_category("Payoffs", 10)
        session.decklist.add_card("Sol Ring", "Ramp")
        # Inject Sol Ring into Draw directly to simulate an inconsistent state
        session.decklist.categories["draw"].cards.append("Sol Ring")
        cmd = _make_cmd(
            "card move Sol Ring Payoffs", "card", "move", ["Sol", "Ring", "Payoffs"]
        )
        result = handle_card_move(session, cmd)
        assert result.startswith("Error:")
        assert "already in the deck" in result
        assert "Draw" in result

    def test_card_move_singleton_check_exempts_basic_lands(self):
        """Basic land cards bypass the singleton non-basic-land rule on card move."""
        session = _make_session_with_deck()
        session.decklist.add_category("Lands", 10)
        session.decklist.add_category("Draw", 10)
        # Inject Forest into two capped categories to simulate an inconsistent state
        session.decklist.categories["lands"].cards.append("Forest")
        session.decklist.categories["draw"].cards.append("Forest")
        # Moving Forest from Lands to Basic Lands should succeed (basic lands are exempt)
        cmd = _make_cmd(
            "card move Forest Basic Lands",
            "card",
            "move",
            ["Forest", "Basic", "Lands"],
        )
        result = handle_card_move(session, cmd)
        assert "Moved" in result
        assert "Forest" in result

    def test_card_move_rejects_basic_land_to_non_basic_lands_category(self):
        """card move rejects moving a basic land to any category other than Basic Lands."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        _add_uncategorized(session, "Forest")
        cmd = _make_cmd(
            "card move Forest Ramp", "card", "move", ["Forest", "Ramp"]
        )
        result = handle_card_move(session, cmd)
        assert result.startswith("Error:")
        assert "Basic Lands" in result

    def test_card_move_allows_basic_land_to_basic_lands_category(self):
        """Moving a basic land from Uncategorized to Basic Lands is permitted (AC 7)."""
        session = _make_session_with_deck()
        _add_uncategorized(session, "Forest")
        cmd = _make_cmd(
            "card move Forest Basic Lands",
            "card",
            "move",
            ["Forest", "Basic", "Lands"],
        )
        result = handle_card_move(session, cmd)
        assert "Moved" in result
        assert "Forest" in session.decklist.categories["basic lands"].cards


class TestCardRemoveHandler:
    """handle_card_remove moves a card to the Uncategorized holding category."""

    def test_card_remove_requires_decklist(self):
        """Returns an error when no decklist is active."""
        session = Session()
        cmd = _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"])
        result = handle_card_remove(session, cmd)
        assert "no active decklist" in result.lower()

    def test_card_remove_returns_error_when_card_not_in_decklist(self):
        """Returns an error when the named card is not in the decklist."""
        session = _make_session_with_deck()
        cmd = _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"])
        result = handle_card_remove(session, cmd)
        assert "not found" in result.lower()

    def test_card_remove_returns_error_when_already_in_uncategorized(self):
        """Returns error and suggests card delete when card is already Uncategorized."""
        session = _make_session_with_deck()
        _add_uncategorized(session, "Sol Ring")
        cmd = _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"])
        result = handle_card_remove(session, cmd)
        assert "uncategorized" in result.lower()
        assert "card delete" in result.lower()

    def test_card_remove_moves_card_to_uncategorized(self):
        """Removes card from its category and places it in Uncategorized."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        cmd = _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"])
        handle_card_remove(session, cmd)
        assert "Sol Ring" not in session.decklist.categories["ramp"].cards
        assert "Sol Ring" in session.decklist.categories["uncategorized"].cards

    def test_card_remove_creates_uncategorized_if_missing(self):
        """Creates the Uncategorized category on demand when it does not exist."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        assert "uncategorized" not in session.decklist.categories
        cmd = _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"])
        handle_card_remove(session, cmd)
        assert "uncategorized" in session.decklist.categories
        cat = session.decklist.categories["uncategorized"]
        assert cat.fixed is True
        assert cat.capped is False
        assert cat.user_addable is False

    def test_card_remove_prints_success_message(self):
        """On success prints the expected message."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        cmd = _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"])
        result = handle_card_remove(session, cmd)
        assert result == (
            "Removed 'Sol Ring' from 'Ramp'. Card is now in Uncategorized."
        )

    def test_card_remove_supports_multi_word_card_name(self):
        """All args after 'remove' are joined as the card name."""
        session = _make_session_with_deck()
        session.decklist.add_card("Atraxa, Praetors' Voice", "Commander")
        cmd = _make_cmd(
            "card remove Atraxa, Praetors' Voice",
            "card",
            "remove",
            ["Atraxa,", "Praetors'", "Voice"],
        )
        result = handle_card_remove(session, cmd)
        assert "Atraxa, Praetors' Voice" in result
        assert "Uncategorized" in result

    def test_card_remove_increments_uncategorized_count(self):
        """After remove, Uncategorized contains one more card than before."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_card("Sol Ring", "Ramp")
        session.decklist.add_card("Mana Crypt", "Ramp")
        _add_uncategorized(session, "Arcane Signet")
        cmd = _make_cmd("card remove Sol Ring", "card", "remove", ["Sol", "Ring"])
        handle_card_remove(session, cmd)
        assert session.decklist.categories["uncategorized"].filled == 2

    def test_card_remove_basic_land_moves_to_uncategorized(self):
        """A basic land can be removed from Basic Lands and placed in Uncategorized."""
        session = _make_session_with_deck()
        session.decklist.add_card("Forest", "Basic Lands")
        cmd = _make_cmd("card remove Forest", "card", "remove", ["Forest"])
        result = handle_card_remove(session, cmd)
        assert "Forest" not in session.decklist.categories["basic lands"].cards
        assert "Forest" in session.decklist.categories["uncategorized"].cards
        assert "Uncategorized" in result


class TestCardDeleteHandler:
    """handle_card_delete permanently removes a card from the decklist."""

    def test_card_delete_requires_decklist(self):
        """Returns an error when no decklist is active."""
        session = Session()
        cmd = _make_cmd("card delete Sol Ring", "card", "delete", ["Sol", "Ring"])
        result = handle_card_delete(session, cmd)
        assert "no active decklist" in result.lower()

    def test_card_delete_returns_error_when_card_not_in_decklist(self):
        """Returns an error when the named card is not in the decklist."""
        session = _make_session_with_deck()
        cmd = _make_cmd("card delete Sol Ring", "card", "delete", ["Sol", "Ring"])
        result = handle_card_delete(session, cmd)
        assert "not found" in result.lower()

    def test_card_delete_removes_card_from_decklist(self):
        """The card is permanently removed from its category."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        cmd = _make_cmd("card delete Sol Ring", "card", "delete", ["Sol", "Ring"])
        handle_card_delete(session, cmd)
        assert "Sol Ring" not in session.decklist.categories["ramp"].cards

    def test_card_delete_prints_success_message(self):
        """On success prints: Deleted '<card>' from the decklist."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        cmd = _make_cmd("card delete Sol Ring", "card", "delete", ["Sol", "Ring"])
        result = handle_card_delete(session, cmd)
        assert result == "Deleted 'Sol Ring' from the decklist."

    def test_card_delete_does_not_place_card_in_uncategorized(self):
        """Deleted card is not added to Uncategorized."""
        session = _make_session_with_card_in_category("Ramp", "Sol Ring")
        cmd = _make_cmd("card delete Sol Ring", "card", "delete", ["Sol", "Ring"])
        handle_card_delete(session, cmd)
        assert "uncategorized" not in session.decklist.categories

    def test_card_delete_removes_from_uncategorized(self):
        """Card can be permanently deleted even when it is in Uncategorized."""
        session = _make_session_with_deck()
        _add_uncategorized(session, "Sol Ring")
        cmd = _make_cmd("card delete Sol Ring", "card", "delete", ["Sol", "Ring"])
        handle_card_delete(session, cmd)
        assert "Sol Ring" not in session.decklist.categories["uncategorized"].cards

    def test_card_delete_supports_multi_word_card_name(self):
        """All args after 'delete' are joined as the card name."""
        session = _make_session_with_deck()
        session.decklist.add_card("Atraxa, Praetors' Voice", "Commander")
        cmd = _make_cmd(
            "card delete Atraxa, Praetors' Voice",
            "card",
            "delete",
            ["Atraxa,", "Praetors'", "Voice"],
        )
        result = handle_card_delete(session, cmd)
        assert "Atraxa, Praetors' Voice" in result
        assert "Atraxa, Praetors' Voice" not in (
            session.decklist.categories["commander"].cards
        )


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
            "card",
            "add",
            ["Basic", "Lands", "Sol", "Ring"],
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
            "card add Basic Lands Forest", "card", "add", ["Basic", "Lands", "Forest"]
        )
        result = handle_card_add(session, cmd)
        assert "Forest" in result
        assert "Basic Lands" in result

    def test_card_add_rejects_non_user_addable_category(self):
        """handle_card_add returns an error for categories with user_addable=False."""
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

    def test_card_add_rejects_basic_land_in_non_basic_lands_category(self):
        """handle_card_add rejects a basic land card added to any category other than Basic Lands."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        cmd = _make_cmd(
            "card add Ramp Forest", "card", "add", ["Ramp", "Forest"]
        )
        result = handle_card_add(session, cmd)
        assert result.startswith("Error:")
        assert "Basic Lands" in result


class TestSavePath:
    def test_default_path_uses_xdg_state_home_fallback(self, monkeypatch, tmp_path):
        """_get_save_path returns ~/.local/state/deckslots/decklist.bak by default."""
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        from pathlib import Path

        path = _get_save_path()
        assert path == Path.home() / ".local" / "state" / "deckslots" / "decklist.bak"

    def test_respects_xdg_state_home_env_var(self, monkeypatch, tmp_path):
        """_get_save_path uses $XDG_STATE_HOME when set."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        path = _get_save_path()
        assert path == tmp_path / "deckslots" / "decklist.bak"


def _make_deck_for_save():
    """Return a Decklist with two user categories, basic lands, and a commander."""
    deck = Decklist.create("Atraxa Stax")
    deck.add_card("Atraxa, Praetors' Voice", "Commander")
    deck.add_category("Ramp", 8)
    deck.add_card("Sol Ring", "Ramp")
    deck.add_card("Cultivate", "Ramp")
    deck.add_category("Removal", 6)
    deck.add_card("Forest", "Basic Lands")
    deck.add_card("Forest", "Basic Lands")
    deck.add_card("Forest", "Basic Lands")
    deck.add_card("Mountain", "Basic Lands")
    return deck


class TestFormatSaveFile:
    def test_first_line_is_name_comment(self):
        """First line of the save file is '# <name>'."""
        deck = Decklist.create("My Deck")
        lines = _format_save_file(deck).splitlines()
        assert lines[0] == "# My Deck"

    def test_commander_section_written(self):
        """Commander section uses bare 'Commander' heading."""
        deck = _make_deck_for_save()
        content = _format_save_file(deck)
        assert "Commander\n1 Atraxa, Praetors' Voice" in content

    def test_basic_lands_follows_commander(self):
        """Basic Lands section appears before user-defined categories."""
        deck = _make_deck_for_save()
        content = _format_save_file(deck)
        assert content.index("Basic Lands") < content.index("Ramp [")

    def test_user_defined_category_heading_includes_slot_count(self):
        """User-defined capped category heading is '<name> [<n> slots]'."""
        deck = _make_deck_for_save()
        content = _format_save_file(deck)
        assert "Ramp [8 slots]" in content

    def test_empty_category_heading_written_without_card_lines(self):
        """An empty category still appears as a heading with no card lines."""
        deck = _make_deck_for_save()
        content = _format_save_file(deck)
        assert "Removal [6 slots]" in content
        lines = content.splitlines()
        removal_idx = lines.index("Removal [6 slots]")
        # Next non-blank line (if any) must not be a card line
        next_lines = [ln for ln in lines[removal_idx + 1 :] if ln.strip()]
        assert not next_lines or not next_lines[0][0].isdigit()

    def test_duplicate_cards_aggregated(self):
        """Multiple copies of the same card are written as a single quantity line."""
        deck = _make_deck_for_save()
        content = _format_save_file(deck)
        assert "3 Forest" in content
        assert "1 Forest" not in content

    def test_uncategorized_written_last_when_present(self):
        """Uncategorized section appears after user-defined categories."""
        from deckslots.models import Category

        deck = _make_deck_for_save()
        deck.categories["uncategorized"] = Category(
            name="Uncategorized",
            total_slots=0,
            fixed=True,
            capped=False,
            user_addable=False,
        )
        deck.categories["uncategorized"].cards.append("Doubling Season")
        content = _format_save_file(deck)
        assert content.index("Uncategorized") > content.index("Ramp [")
        assert "Doubling Season" in content

    def test_sections_separated_by_blank_line(self):
        """Each section is separated from the next by exactly one blank line."""
        deck = _make_deck_for_save()
        content = _format_save_file(deck)
        assert "\n\n" in content
        assert "\n\n\n" not in content


class TestDecklistSaveHandler:
    def test_save_requires_active_decklist(self):
        """handle_decklist_save returns an error when no decklist is active."""
        session = Session()
        cmd = _make_cmd("decklist save", "decklist", "save", [])
        result = handle_decklist_save(session, cmd)
        assert "no active decklist" in result.lower()

    def test_save_writes_file_to_xdg_path(self, monkeypatch, tmp_path):
        """handle_decklist_save writes the save file to the XDG state path."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        session = _make_session_with_deck()
        cmd = _make_cmd("decklist save", "decklist", "save", [])
        handle_decklist_save(session, cmd)
        save_file = tmp_path / "deckslots" / "decklist.bak"
        assert save_file.exists()

    def test_save_creates_parent_directory(self, monkeypatch, tmp_path):
        """handle_decklist_save creates the parent directory if absent."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
        session = _make_session_with_deck()
        cmd = _make_cmd("decklist save", "decklist", "save", [])
        handle_decklist_save(session, cmd)
        assert (tmp_path / "state" / "deckslots" / "decklist.bak").exists()

    def test_save_returns_success_message(self, monkeypatch, tmp_path):
        """handle_decklist_save returns \"Saved '<name>'.\" on success."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        session = _make_session_with_deck()
        cmd = _make_cmd("decklist save", "decklist", "save", [])
        result = handle_decklist_save(session, cmd)
        assert result == "Saved 'TestDeck'."

    def test_save_overwrites_existing_file(self, monkeypatch, tmp_path):
        """handle_decklist_save silently overwrites an existing save file."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        save_file = tmp_path / "deckslots" / "decklist.bak"
        save_file.parent.mkdir(parents=True)
        save_file.write_text("old content")
        session = _make_session_with_deck()
        cmd = _make_cmd("decklist save", "decklist", "save", [])
        handle_decklist_save(session, cmd)
        assert save_file.read_text() != "old content"

    def test_save_registered_in_dispatch(self, monkeypatch, tmp_path):
        """decklist save is dispatchable via the registry."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        cmd = _make_cmd("decklist save", "decklist", "save", [])
        result = dispatch(cmd, registry)
        assert "Saved" in result


def _write_save_file(path, content):
    """Write content to a file at path, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestParseSaveFile:
    def test_raises_file_not_found(self, tmp_path):
        """_parse_save_file raises FileNotFoundError for a missing path."""
        with pytest.raises(FileNotFoundError):
            _parse_save_file(str(tmp_path / "missing.bak"))

    def test_raises_value_error_without_name_line(self, tmp_path):
        """_parse_save_file raises ValueError when the # <name> line is absent."""
        f = tmp_path / "deck.bak"
        f.write_text("Commander\n1 Atraxa, Praetors' Voice\n")
        with pytest.raises(ValueError, match="name"):
            _parse_save_file(str(f))

    def test_restores_decklist_name(self, tmp_path):
        """_parse_save_file uses the # <name> line as the decklist name."""
        f = tmp_path / "deck.bak"
        f.write_text("# Atraxa Stax\n\nCommander\n")
        deck = _parse_save_file(str(f))
        assert deck.name == "Atraxa Stax"

    def test_restores_commander_card(self, tmp_path):
        """_parse_save_file adds the commander card to the Commander category."""
        f = tmp_path / "deck.bak"
        f.write_text("# Test\n\nCommander\n1 Atraxa, Praetors' Voice\n")
        deck = _parse_save_file(str(f))
        assert "Atraxa, Praetors' Voice" in deck.categories["commander"].cards

    def test_restores_basic_lands(self, tmp_path):
        """_parse_save_file adds basic land cards to the Basic Lands category."""
        f = tmp_path / "deck.bak"
        f.write_text("# Test\n\nCommander\n\nBasic Lands\n3 Forest\n1 Mountain\n")
        deck = _parse_save_file(str(f))
        assert deck.categories["basic lands"].cards.count("Forest") == 3
        assert deck.categories["basic lands"].cards.count("Mountain") == 1

    def test_basic_lands_appear_before_user_categories_in_dict(self, tmp_path):
        """Basic Lands section is parsed before user-defined categories."""
        f = tmp_path / "deck.bak"
        content = (
            "# Test\n\nCommander\n\nBasic Lands\n2 Forest\n\n"
            "Ramp [8 slots]\n1 Sol Ring\n"
        )
        f.write_text(content)
        deck = _parse_save_file(str(f))
        keys = list(deck.categories)
        assert keys.index("basic lands") < keys.index("ramp")

    def test_restores_user_defined_category_with_slot_count(self, tmp_path):
        """_parse_save_file creates a user-defined category with correct total_slots."""
        f = tmp_path / "deck.bak"
        f.write_text("# Test\n\nCommander\n\nRamp [8 slots]\n1 Sol Ring\n")
        deck = _parse_save_file(str(f))
        assert "ramp" in deck.categories
        assert deck.categories["ramp"].total_slots == 8
        assert "Sol Ring" in deck.categories["ramp"].cards

    def test_restores_uncategorized(self, tmp_path):
        """_parse_save_file creates the Uncategorized category when present."""
        f = tmp_path / "deck.bak"
        f.write_text("# Test\n\nCommander\n\nUncategorized\n1 Doubling Season\n")
        deck = _parse_save_file(str(f))
        cat = deck.categories["uncategorized"]
        assert not cat.capped
        assert not cat.user_addable
        assert "Doubling Season" in cat.cards

    def test_aggregated_quantity_expanded_to_multiple_entries(self, tmp_path):
        """'3 Forest' in the save file is restored as three separate list entries."""
        f = tmp_path / "deck.bak"
        f.write_text("# Test\n\nCommander\n\nBasic Lands\n3 Forest\n")
        deck = _parse_save_file(str(f))
        assert deck.categories["basic lands"].cards.count("Forest") == 3

    def test_non_basic_land_under_basic_lands_raises(self, tmp_path):
        """A non-basic-land card under Basic Lands raises ValueError."""
        f = tmp_path / "deck.bak"
        f.write_text("# Test\n\nBasic Lands\n1 Sol Ring\n")
        with pytest.raises(ValueError):
            _parse_save_file(str(f))

    def test_blank_and_unrecognised_lines_skipped(self, tmp_path):
        """Blank lines and unrecognised lines are silently skipped."""
        f = tmp_path / "deck.bak"
        f.write_text(
            "# Test\n\nCommander\n\n# stray comment\n1 Atraxa, Praetors' Voice\n"
        )
        deck = _parse_save_file(str(f))
        assert "Atraxa, Praetors' Voice" in deck.categories["commander"].cards

    def test_round_trip_preserves_full_deck(self, tmp_path):
        """A deck serialised then parsed is identical to the original."""
        original = _make_deck_for_save()
        content = _format_save_file(original)
        f = tmp_path / "deck.bak"
        f.write_text(content)
        restored = _parse_save_file(str(f))
        assert restored.name == original.name
        assert set(restored.categories) == set(original.categories)
        for key, cat in original.categories.items():
            assert sorted(restored.categories[key].cards) == sorted(cat.cards)
            assert restored.categories[key].total_slots == cat.total_slots


class TestDecklistLoadHandler:
    def _save_deck(self, deck, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        save_file = tmp_path / "deckslots" / "decklist.bak"
        save_file.parent.mkdir(parents=True)
        save_file.write_text(_format_save_file(deck))

    def test_load_returns_error_when_no_save_file(self, monkeypatch, tmp_path):
        """handle_decklist_load returns an error when no save file exists."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        session = Session()
        cmd = _make_cmd("decklist load", "decklist", "load", [])
        result = handle_decklist_load(session, cmd)
        assert "no saved decklist" in result.lower()

    def test_load_returns_error_on_parse_failure(self, monkeypatch, tmp_path):
        """handle_decklist_load returns an error for an unparseable file."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        save_file = tmp_path / "deckslots" / "decklist.bak"
        save_file.parent.mkdir(parents=True)
        save_file.write_text("this is not a valid save file\n")
        session = Session()
        cmd = _make_cmd("decklist load", "decklist", "load", [])
        result = handle_decklist_load(session, cmd)
        assert "error" in result.lower()

    def test_load_restores_decklist(self, monkeypatch, tmp_path):
        """handle_decklist_load sets session.decklist from the save file."""
        original = _make_deck_for_save()
        self._save_deck(original, tmp_path, monkeypatch)
        session = Session()
        cmd = _make_cmd("decklist load", "decklist", "load", [])
        handle_decklist_load(session, cmd)
        assert session.decklist is not None
        assert session.decklist.name == "Atraxa Stax"

    def test_load_returns_success_message(self, monkeypatch, tmp_path):
        """handle_decklist_load returns \"Loaded '<name>'.\" on success."""
        original = _make_deck_for_save()
        self._save_deck(original, tmp_path, monkeypatch)
        session = Session()
        cmd = _make_cmd("decklist load", "decklist", "load", [])
        result = handle_decklist_load(session, cmd)
        assert result == "Loaded 'Atraxa Stax'."

    def test_load_replaces_active_decklist(self, monkeypatch, tmp_path):
        """handle_decklist_load replaces any currently active decklist."""
        original = _make_deck_for_save()
        self._save_deck(original, tmp_path, monkeypatch)
        session = _make_session_with_deck()  # has a different active deck
        cmd = _make_cmd("decklist load", "decklist", "load", [])
        handle_decklist_load(session, cmd)
        assert session.decklist.name == "Atraxa Stax"

    def test_load_registered_in_dispatch(self, monkeypatch, tmp_path):
        """decklist load is dispatchable via the registry."""
        original = _make_deck_for_save()
        self._save_deck(original, tmp_path, monkeypatch)
        session = Session()
        registry = register_all_handlers(session)
        cmd = _make_cmd("decklist load", "decklist", "load", [])
        result = dispatch(cmd, registry)
        assert "Loaded" in result


class TestFormatExportFile:
    """_format_export_file produces a two-section Commander/Maindeck export."""

    def test_empty_decklist_produces_two_sections(self):
        """Even with no cards the output has Commander and Maindeck headers."""
        deck = Decklist.create("TestDeck")
        result = _format_export_file(deck)
        assert result == "Commander\n\nMaindeck\n"

    def test_commander_card_appears_in_commander_section(self):
        """A card in the Commander category appears under the Commander header."""
        deck = Decklist.create("TestDeck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        result = _format_export_file(deck)
        assert "Commander\n1 Atraxa, Praetors' Voice\n" in result

    def test_no_commander_assigned_commander_section_is_empty(self):
        """With no commander card the Commander section header has no card lines."""
        deck = Decklist.create("TestDeck")
        result = _format_export_file(deck)
        lines = result.split("\n")
        commander_idx = lines.index("Commander")
        assert lines[commander_idx + 1] == ""

    def test_capped_category_cards_appear_in_maindeck(self):
        """Cards in a user-defined category appear in the Maindeck section."""
        deck = Decklist.create("TestDeck")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        result = _format_export_file(deck)
        assert "Maindeck\n1 Sol Ring\n" in result

    def test_basic_land_duplicates_aggregated(self):
        """Multiple copies of a basic land are aggregated into a single qty line."""
        deck = Decklist.create("TestDeck")
        for _ in range(3):
            deck.add_card("Forest", "Basic Lands")
        result = _format_export_file(deck)
        assert "3 Forest" in result
        assert "1 Forest" not in result

    def test_maindeck_cards_sorted_alphabetically(self):
        """Maindeck card lines appear in alphabetical order by card name."""
        deck = Decklist.create("TestDeck")
        deck.add_category("Ramp", 10)
        deck.add_card("Sol Ring", "Ramp")
        deck.add_card("Cultivate", "Ramp")
        result = _format_export_file(deck)
        maindeck_start = result.index("Maindeck\n") + len("Maindeck\n")
        maindeck_body = result[maindeck_start:]
        card_lines = [ln for ln in maindeck_body.strip().split("\n") if ln]
        assert card_lines == sorted(card_lines)

    def test_category_names_and_slot_counts_not_written(self):
        """Category names (other than Commander / Maindeck) do not appear in output."""
        deck = Decklist.create("TestDeck")
        deck.add_category("Ramp", 5)
        deck.add_card("Sol Ring", "Ramp")
        result = _format_export_file(deck)
        assert "Ramp" not in result
        assert "[5 slots]" not in result

    def test_cards_aggregated_across_categories(self):
        """The same card name in two categories yields one aggregated Maindeck line."""
        deck = Decklist.create("TestDeck")
        # Basic Lands and Uncategorized are both uncapped, so Forest can appear in both
        deck.add_card("Forest", "Basic Lands")
        deck.add_card("Forest", "Basic Lands")
        deck.categories["uncategorized"] = Category(
            name="Uncategorized",
            total_slots=0,
            fixed=True,
            capped=False,
            user_addable=False,
        )
        deck.categories["uncategorized"].cards.append("Forest")
        result = _format_export_file(deck)
        assert "3 Forest" in result


class TestHandleDecklistExport:
    """handle_decklist_export writes the deck to a file and returns confirmation."""

    def test_no_decklist_returns_error(self):
        """Returns an error when no decklist is active."""
        session = Session()
        cmd = _make_cmd(
            "decklist export /tmp/x.txt", "decklist", "export", ["/tmp/x.txt"]
        )
        result = handle_decklist_export(session, cmd)
        assert result == "No active decklist. Use 'decklist create <name>' first."

    def test_no_args_returns_usage(self):
        """Returns a usage message when no filepath is supplied."""
        session = _make_session_with_deck()
        cmd = _make_cmd("decklist export", "decklist", "export", [])
        result = handle_decklist_export(session, cmd)
        assert result == "Usage: decklist export <filepath>"

    def test_export_writes_file(self, tmp_path):
        """The export file is created at the given path."""
        session = _make_session_with_deck()
        out = tmp_path / "deck.txt"
        cmd = _make_cmd(f"decklist export {out}", "decklist", "export", [str(out)])
        handle_decklist_export(session, cmd)
        assert out.exists()

    def test_export_returns_confirmation_with_name_and_path(self, tmp_path):
        """Returns \"Exported '<name>' to '<filepath>'.\" on success."""
        session = _make_session_with_deck()
        out = tmp_path / "deck.txt"
        cmd = _make_cmd(f"decklist export {out}", "decklist", "export", [str(out)])
        result = handle_decklist_export(session, cmd)
        assert result == f"Exported 'TestDeck' to '{out}'."

    def test_export_file_contents_match_format_function(self, tmp_path):
        """File contents equal _format_export_file(session.decklist)."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 5)
        session.decklist.add_card("Sol Ring", "Ramp")
        out = tmp_path / "deck.txt"
        cmd = _make_cmd(f"decklist export {out}", "decklist", "export", [str(out)])
        handle_decklist_export(session, cmd)
        assert out.read_text() == _format_export_file(session.decklist)

    def test_export_creates_parent_directory(self, tmp_path):
        """Parent directory is created automatically if it does not exist."""
        session = _make_session_with_deck()
        out = tmp_path / "subdir" / "deck.txt"
        cmd = _make_cmd(f"decklist export {out}", "decklist", "export", [str(out)])
        handle_decklist_export(session, cmd)
        assert out.exists()

    def test_export_path_assembled_from_multi_token_args(self, tmp_path):
        """Filepath args with spaces are joined into a single path."""
        session = _make_session_with_deck()
        out = tmp_path / "my deck.txt"
        args = [str(tmp_path), "my deck.txt"]
        # Simulate args that would reconstruct the path when joined
        args = str(out).split(" ")
        cmd = _make_cmd(f"decklist export {out}", "decklist", "export", args)
        handle_decklist_export(session, cmd)
        assert out.exists()

    def test_export_registered_in_dispatch(self, tmp_path):
        """decklist export is dispatchable via the registry."""
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        out = tmp_path / "deck.txt"
        cmd = _make_cmd(f"decklist export {out}", "decklist", "export", [str(out)])
        result = dispatch(cmd, registry)
        assert "Exported" in result
