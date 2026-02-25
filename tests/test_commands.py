import pytest

from deckslots.cli import ParsedCommand
from deckslots.commands import (
    Session,
    _parse_import_file,
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
    handle_decklist_import,
    handle_decklist_show,
    handle_help,
    register_all_handlers,
)
from deckslots.models import Category


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
        result = _resolve_card_and_category_suffix(
            ["Sol", "Ring", "Big", "Ramp"], cats
        )
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
