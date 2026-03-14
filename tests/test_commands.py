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
    handle_category_rename,
    handle_decklist_apply_template,
    handle_decklist_create,
    handle_decklist_disable_background,
    handle_decklist_disable_companion,
    handle_decklist_disable_partners,
    handle_decklist_enable_background,
    handle_decklist_enable_companion,
    handle_decklist_enable_partners,
    handle_decklist_export,
    handle_decklist_import,
    handle_decklist_load,
    handle_decklist_rename,
    handle_decklist_save,
    handle_decklist_show,
    handle_help,
    handle_template_export,
    handle_template_import,
    handle_template_list,
    handle_template_save,
    register_all_handlers,
    validate_category_rename,
    validate_decklist_rename,
    validate_template_save,
)
from deckslots.models import CappedCategory, Decklist, UncappedCategory


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

    def test_parse_import_recognizes_companion_heading(self, tmp_path):
        """A Companion section card is returned as companion."""
        f = tmp_path / "deck.txt"
        f.write_text(
            "Commander\n1 Atraxa\n\n"
            "Companion\n1 Lurrus of the Dream-Den\n\n"
            "Maindeck\n1 Sol Ring\n"
        )
        result = _parse_import_file(str(f))
        assert result.companion == "Lurrus of the Dream-Den"

    def test_parse_import_companion_not_in_uncategorized(self, tmp_path):
        """The companion card does NOT appear in the uncategorized list."""
        f = tmp_path / "deck.txt"
        f.write_text(
            "Commander\n1 Atraxa\n\n"
            "Companion\n1 Lurrus of the Dream-Den\n\n"
            "Maindeck\n1 Sol Ring\n"
        )
        result = _parse_import_file(str(f))
        assert "Lurrus of the Dream-Den" not in result.uncategorized

    def test_parse_import_no_companion_heading_leaves_companion_none(self, tmp_path):
        """When no Companion section is present, companion is None."""
        f = tmp_path / "deck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        result = _parse_import_file(str(f))
        assert result.companion is None


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
        f.write_text("Commander\n1 Atraxa, Praetors' Voice\n\nMaindeck\n1 Sol Ring\n")
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
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n2 Arcane Signet\n")
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
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n4 Forest\n")
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

    def test_import_enables_companion_when_companion_card_present(self, tmp_path):
        """After importing with a Companion section, companion_enabled is True."""
        f = tmp_path / "deck.txt"
        f.write_text(
            "Commander\n1 Atraxa\n\n"
            "Companion\n1 Lurrus of the Dream-Den\n\n"
            "Maindeck\n1 Sol Ring\n"
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
        assert session.decklist.companion_enabled is True

    def test_import_adds_companion_card_to_companion_category(self, tmp_path):
        """The imported companion card lands in the Companion category."""
        f = tmp_path / "deck.txt"
        f.write_text(
            "Commander\n1 Atraxa\n\n"
            "Companion\n1 Lurrus of the Dream-Den\n\n"
            "Maindeck\n1 Sol Ring\n"
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
        companion_cards = session.decklist.categories["companion"].cards
        assert "Lurrus of the Dream-Den" in companion_cards


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

    def test_help_includes_enable_background(self):
        """The help output includes the enable-background command."""
        result = handle_help()
        assert "enable-background" in result

    def test_help_includes_disable_partners(self):
        """The help output includes the disable-partners command."""
        result = handle_help()
        assert "disable-partners" in result

    def test_help_includes_disable_background(self):
        """The help output includes the disable-background command."""
        result = handle_help()
        assert "disable-background" in result


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
    session.decklist.categories["uncategorized"] = UncappedCategory(
        name="Uncategorized",
        fixed=True,
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

    def test_card_move_singleton_check_exempts_basic_lands(self):
        """Basic land cards bypass the singleton non-basic-land rule on card move."""
        session = _make_session_with_deck()
        session.decklist.add_category("Lands", 10)
        session.decklist.add_category("Draw", 10)
        # Inject Forest into two capped categories to simulate an inconsistent state
        session.decklist.categories["lands"].cards.append("Forest")
        session.decklist.categories["draw"].cards.append("Forest")
        # Moving Forest to Basic Lands should succeed (basic lands are exempt)
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
        """card move rejects moving a basic land to a non-Basic-Lands category."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        _add_uncategorized(session, "Forest")
        cmd = _make_cmd("card move Forest Ramp", "card", "move", ["Forest", "Ramp"])
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
        assert isinstance(cat, UncappedCategory)
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
        session.decklist.categories["uncategorized"] = UncappedCategory(
            name="Uncategorized",
            fixed=True,
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
        """handle_card_add rejects a basic land added to a non-Basic-Lands category."""
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        cmd = _make_cmd("card add Ramp Forest", "card", "add", ["Ramp", "Forest"])
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
        deck = _make_deck_for_save()
        deck.categories["uncategorized"] = UncappedCategory(
            name="Uncategorized",
            fixed=True,
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
        ramp = deck.categories["ramp"]
        assert isinstance(ramp, CappedCategory)
        assert ramp.total_slots == 8
        assert "Sol Ring" in ramp.cards

    def test_restores_uncategorized(self, tmp_path):
        """_parse_save_file creates the Uncategorized category when present."""
        f = tmp_path / "deck.bak"
        f.write_text("# Test\n\nCommander\n\nUncategorized\n1 Doubling Season\n")
        deck = _parse_save_file(str(f))
        cat = deck.categories["uncategorized"]
        assert isinstance(cat, UncappedCategory)
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
            restored_cat = restored.categories[key]
            if isinstance(cat, CappedCategory) and isinstance(
                restored_cat, CappedCategory
            ):
                assert restored_cat.total_slots == cat.total_slots


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
        deck.categories["uncategorized"] = UncappedCategory(
            name="Uncategorized",
            fixed=True,
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


class TestValidateDecklistRename:
    def test_no_decklist_returns_error(self):
        session = Session()
        result = validate_decklist_rename(session)
        assert result == "No active decklist. Use 'decklist create <name>' first."

    def test_active_decklist_returns_none(self):
        session = _make_session_with_deck()
        assert validate_decklist_rename(session) is None


class TestValidateCategoryRename:
    def test_no_decklist_returns_error(self):
        session = Session()
        result = validate_category_rename(session, "ramp")
        assert result == "No active decklist. Use 'decklist create <name>' first."

    def test_empty_old_name_returns_usage(self):
        session = _make_session_with_deck()
        result = validate_category_rename(session, "")
        assert result == "Usage: category rename <name>"

    def test_not_found_returns_error(self):
        session = _make_session_with_deck()
        result = validate_category_rename(session, "nonexistent")
        assert result is not None
        assert "not found" in result

    def test_fixed_category_returns_error(self):
        session = _make_session_with_deck()
        result = validate_category_rename(session, "commander")
        assert result is not None
        assert "Cannot rename fixed category" in result

    def test_valid_user_category_returns_none(self):
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        assert validate_category_rename(session, "ramp") is None


class TestHandleDecklistRename:
    def test_renames_decklist(self):
        session = _make_session_with_deck()
        result = handle_decklist_rename(session, "New Name")
        assert result == "Renamed decklist to 'New Name'."
        assert session.decklist.name == "New Name"

    def test_empty_name_returns_error_without_renaming(self):
        session = _make_session_with_deck()
        result = handle_decklist_rename(session, "")
        assert result == "Name cannot be empty."
        assert session.decklist.name == "TestDeck"  # unchanged


class TestHandleCategoryRename:
    def test_renames_category(self):
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        result = handle_category_rename(session, "ramp", "Mana Rocks")
        assert result == "Renamed category 'Ramp' to 'Mana Rocks'."
        assert "mana rocks" in session.decklist.categories
        assert "ramp" not in session.decklist.categories

    def test_shows_original_display_name_in_message(self):
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        # old_name passed as lowercase, but message shows stored display name
        result = handle_category_rename(session, "ramp", "Mana Rocks")
        assert "'Ramp'" in result  # original display name, not "ramp"

    def test_empty_new_name_returns_error_without_renaming(self):
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        result = handle_category_rename(session, "ramp", "")
        assert result == "Name cannot be empty."
        assert "ramp" in session.decklist.categories  # unchanged

    def test_conflicting_new_name_returns_error(self):
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        session.decklist.add_category("Combo", 10)
        result = handle_category_rename(session, "ramp", "Combo")
        assert "already exists" in result
        assert "ramp" in session.decklist.categories  # unchanged


class TestFormatExportFilePartners:
    """_format_export_file lists both commanders when partners is enabled."""

    def test_export_with_two_commanders_lists_both(self):
        """Both partner commanders appear in the Commander export section."""
        deck = Decklist.create("Partner Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        content = _format_export_file(deck)
        assert "1 Malcolm, Keen-Eyed Navigator" in content
        assert "1 Tana, the Bloodsower" in content

    def test_export_two_commanders_not_in_maindeck(self):
        """Partner commanders do not appear in the Maindeck export section."""
        deck = Decklist.create("Partner Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        content = _format_export_file(deck)
        maindeck_start = content.index("Maindeck")
        maindeck_section = content[maindeck_start:]
        assert "Malcolm" not in maindeck_section
        assert "Tana" not in maindeck_section

    def test_export_single_commander_unchanged(self):
        """A single-commander decklist still exports the commander as before."""
        deck = Decklist.create("Solo Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        content = _format_export_file(deck)
        assert "1 Atraxa, Praetors' Voice" in content
        commander_section = content[: content.index("Maindeck")]
        assert commander_section.count("1 ") == 1


class TestFormatExportFileCompanion:
    """_format_export_file emits a Companion section when a companion is present."""

    def test_export_includes_companion_section(self):
        """Export output contains a 'Companion' heading when companion is enabled."""
        deck = Decklist.create("Companion Deck")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        content = _format_export_file(deck)
        assert "Companion\n" in content

    def test_export_companion_card_appears_under_companion_heading(self):
        """The companion card appears in the Companion section, not Maindeck."""
        deck = Decklist.create("Companion Deck")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        content = _format_export_file(deck)
        assert "Companion\n1 Lurrus of the Dream-Den" in content

    def test_export_companion_card_excluded_from_maindeck(self):
        """The companion card does NOT appear in the Maindeck section."""
        deck = Decklist.create("Companion Deck")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        content = _format_export_file(deck)
        maindeck_start = content.index("Maindeck")
        maindeck_section = content[maindeck_start:]
        assert "Lurrus" not in maindeck_section

    def test_export_empty_companion_has_no_companion_section(self):
        """An enabled but empty companion slot produces no Companion section."""
        deck = Decklist.create("Companion Deck")
        deck.enable_companion()
        content = _format_export_file(deck)
        assert "Companion\n" not in content


class TestFormatSaveFilePartners:
    """_format_save_file always writes plain Commander; load sets slots dynamically."""

    def test_partners_disabled_uses_plain_heading(self):
        """When partners is off, Commander section heading is plain 'Commander'."""
        deck = Decklist.create("My Deck")
        content = _format_save_file(deck)
        assert "Commander [partners]" not in content
        assert "Commander" in content

    def test_save_always_uses_plain_commander_heading(self):
        """Commander section heading is always plain 'Commander' regardless of mode."""
        deck_partners = Decklist.create("Partner Deck")
        deck_partners.enable_partners()
        assert "Commander" in _format_save_file(deck_partners)
        assert "Commander [partners]" not in _format_save_file(deck_partners)

    def test_load_ignores_partners_tag_and_dynamically_allocates_slots(self, tmp_path):
        """Loading a file with 'Commander [partners]' ignores the tag;
        Commander slots are set from the number of loaded cards."""
        content = (
            "# Partner Deck\n\n"
            "Commander [partners]\n"
            "1 Malcolm, Keen-Eyed Navigator\n"
            "1 Tana, the Bloodsower\n\n"
            "Basic Lands\n"
        )
        path = tmp_path / "deck.bak"
        path.write_text(content)
        loaded = _parse_save_file(str(path))
        assert loaded.partners_enabled is False  # tag is ignored
        assert loaded.categories["commander"].total_slots == 2  # dynamic
        assert "Malcolm, Keen-Eyed Navigator" in loaded.categories["commander"].cards
        assert "Tana, the Bloodsower" in loaded.categories["commander"].cards

    def test_load_sets_commander_slots_from_card_count(self, tmp_path):
        """Loading a plain Commander section with 2 cards sets total_slots to 2."""
        content = (
            "# My Deck\n\n"
            "Commander\n"
            "1 Malcolm, Keen-Eyed Navigator\n"
            "1 Tana, the Bloodsower\n\n"
            "Basic Lands\n"
        )
        path = tmp_path / "deck.bak"
        path.write_text(content)
        loaded = _parse_save_file(str(path))
        assert loaded.categories["commander"].total_slots == 2
        assert loaded.partners_enabled is False

    def test_load_with_one_commander_keeps_one_slot(self, tmp_path):
        """Loading a Commander section with 1 card keeps total_slots at 1."""
        deck = Decklist.create("Solo Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        path = tmp_path / "deck.bak"
        path.write_text(_format_save_file(deck))
        loaded = _parse_save_file(str(path))
        assert loaded.categories["commander"].total_slots == 1

    def test_parse_save_file_restores_both_commanders(self, tmp_path):
        """Both partner commanders are loaded back into the Commander category."""
        deck = Decklist.create("Partner Deck")
        deck.enable_partners()
        deck.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        deck.add_card("Tana, the Bloodsower", "Commander")
        path = tmp_path / "deck.bak"
        path.write_text(_format_save_file(deck))
        loaded = _parse_save_file(str(path))
        assert "Malcolm, Keen-Eyed Navigator" in loaded.categories["commander"].cards
        assert "Tana, the Bloodsower" in loaded.categories["commander"].cards

    def test_parse_save_file_partners_disabled_stays_false(self, tmp_path):
        """Parsing a save file without partners flag keeps partners_enabled False."""
        deck = Decklist.create("Solo Deck")
        deck.add_card("Atraxa, Praetors' Voice", "Commander")
        path = tmp_path / "deck.bak"
        path.write_text(_format_save_file(deck))
        loaded = _parse_save_file(str(path))
        assert loaded.partners_enabled is False


class TestFormatSaveFileCompanion:
    """_format_save_file writes Companion with a plain heading."""

    def test_companion_section_uses_plain_heading(self, tmp_path):
        """Companion section heading is plain 'Companion', not 'Companion [1 slots]'."""
        deck = Decklist.create("Companion Deck")
        deck.enable_companion()
        content = _format_save_file(deck)
        lines = content.splitlines()
        assert "Companion" in lines
        assert "Companion [1 slots]" not in lines

    def test_companion_card_written_under_companion_heading(self, tmp_path):
        """The companion card appears under the Companion heading."""
        deck = Decklist.create("Companion Deck")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        content = _format_save_file(deck)
        assert "Companion\n1 Lurrus of the Dream-Den" in content


class TestParseSaveFileCompanion:
    """_parse_save_file recognises the Companion heading and enables companion mode."""

    def test_parse_companion_heading_enables_companion(self, tmp_path):
        """Parsing a Companion section sets companion_enabled to True."""
        content = (
            "# My Deck\n\n"
            "Commander\n\n"
            "Basic Lands\n\n"
            "Companion\n"
            "1 Lurrus of the Dream-Den\n"
        )
        path = tmp_path / "deck.bak"
        path.write_text(content)
        loaded = _parse_save_file(str(path))
        assert loaded.companion_enabled is True
        assert "companion" in loaded.categories

    def test_parse_companion_card_placed_in_companion_category(self, tmp_path):
        """The companion card is placed in the Companion category, not Commander."""
        content = (
            "# My Deck\n\n"
            "Commander\n\n"
            "Basic Lands\n\n"
            "Companion\n"
            "1 Lurrus of the Dream-Den\n"
        )
        path = tmp_path / "deck.bak"
        path.write_text(content)
        loaded = _parse_save_file(str(path))
        assert "Lurrus of the Dream-Den" in loaded.categories["companion"].cards

    def test_round_trip_preserves_companion(self, tmp_path):
        """save then load preserves companion_enabled and the companion card."""
        deck = Decklist.create("Round Trip Deck")
        deck.enable_companion()
        deck.add_card("Lurrus of the Dream-Den", "Companion")
        path = tmp_path / "deck.bak"
        path.write_text(_format_save_file(deck))
        loaded = _parse_save_file(str(path))
        assert loaded.companion_enabled is True
        assert "Lurrus of the Dream-Den" in loaded.categories["companion"].cards

    def test_no_companion_heading_leaves_companion_disabled(self, tmp_path):
        """Parsing a file without a Companion section leaves companion_enabled False."""
        deck = Decklist.create("Solo Deck")
        path = tmp_path / "deck.bak"
        path.write_text(_format_save_file(deck))
        loaded = _parse_save_file(str(path))
        assert loaded.companion_enabled is False


class TestHandleDecklistEnablePartners:
    """handle_decklist_enable_partners enables partner commanders."""

    def _cmd(self) -> ParsedCommand:
        return ParsedCommand(
            kind="object_verb",
            raw="decklist enable-partners",
            obj="decklist",
            verb="enable-partners",
            args=[],
        )

    def test_returns_error_when_no_active_decklist(self):
        """Returns an error message when no decklist exists."""
        session = Session()
        result = handle_decklist_enable_partners(session, self._cmd())
        assert "No active decklist" in result

    def test_sets_partners_enabled_on_decklist(self):
        """Calling the handler sets partners_enabled to True."""
        session = _make_session_with_deck()
        handle_decklist_enable_partners(session, self._cmd())
        assert session.decklist.partners_enabled is True

    def test_commander_category_has_two_slots_after_enable(self):
        """After the handler runs, the Commander category has 2 slots."""
        session = _make_session_with_deck()
        handle_decklist_enable_partners(session, self._cmd())
        assert session.decklist.categories["commander"].total_slots == 2

    def test_returns_confirmation_message(self):
        """Handler returns a human-readable success message."""
        session = _make_session_with_deck()
        result = handle_decklist_enable_partners(session, self._cmd())
        assert "partner" in result.lower()

    def test_registered_in_dispatch_table(self):
        """enable-partners is registered in the dispatch registry."""
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "enable-partners") in registry


class TestHandleDecklistEnableBackground:
    """handle_decklist_enable_background enables background commanders."""

    def _cmd(self) -> ParsedCommand:
        return ParsedCommand(
            kind="object_verb",
            raw="decklist enable-background",
            obj="decklist",
            verb="enable-background",
            args=[],
        )

    def test_returns_error_when_no_active_decklist(self):
        session = Session()
        result = handle_decklist_enable_background(session, self._cmd())
        assert "No active decklist" in result

    def test_sets_background_enabled_on_decklist(self):
        session = _make_session_with_deck()
        handle_decklist_enable_background(session, self._cmd())
        assert session.decklist.background_enabled is True

    def test_commander_category_has_two_slots_after_enable(self):
        session = _make_session_with_deck()
        handle_decklist_enable_background(session, self._cmd())
        assert session.decklist.categories["commander"].total_slots == 2

    def test_returns_confirmation_message(self):
        session = _make_session_with_deck()
        result = handle_decklist_enable_background(session, self._cmd())
        assert "background" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "enable-background") in registry


class TestHandleDecklistDisablePartners:
    """handle_decklist_disable_partners disables partner mode and evacuates them."""

    def _cmd(self) -> ParsedCommand:
        return ParsedCommand(
            kind="object_verb",
            raw="decklist disable-partners",
            obj="decklist",
            verb="disable-partners",
            args=[],
        )

    def test_returns_error_when_no_active_decklist(self):
        session = Session()
        result = handle_decklist_disable_partners(session, self._cmd())
        assert "No active decklist" in result

    def test_clears_partners_enabled(self):
        session = _make_session_with_deck()
        session.decklist.enable_partners()
        handle_decklist_disable_partners(session, self._cmd())
        assert session.decklist.partners_enabled is False

    def test_commander_cards_move_to_uncategorized(self):
        session = _make_session_with_deck()
        session.decklist.enable_partners()
        session.decklist.add_card("Malcolm, Keen-Eyed Navigator", "Commander")
        session.decklist.add_card("Tana, the Bloodsower", "Commander")
        handle_decklist_disable_partners(session, self._cmd())
        assert session.decklist.categories["commander"].cards == []
        uncat = session.decklist.categories["uncategorized"].cards
        assert "Malcolm, Keen-Eyed Navigator" in uncat

    def test_returns_confirmation_message(self):
        session = _make_session_with_deck()
        session.decklist.enable_partners()
        result = handle_decklist_disable_partners(session, self._cmd())
        assert "uncategorized" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "disable-partners") in registry


class TestHandleDecklistDisableBackground:
    """handle_decklist_disable_background disables background mode and evacuates
    commanders."""

    def _cmd(self) -> ParsedCommand:
        return ParsedCommand(
            kind="object_verb",
            raw="decklist disable-background",
            obj="decklist",
            verb="disable-background",
            args=[],
        )

    def test_returns_error_when_no_active_decklist(self):
        session = Session()
        result = handle_decklist_disable_background(session, self._cmd())
        assert "No active decklist" in result

    def test_clears_background_enabled(self):
        session = _make_session_with_deck()
        session.decklist.enable_background()
        handle_decklist_disable_background(session, self._cmd())
        assert session.decklist.background_enabled is False

    def test_commander_cards_move_to_uncategorized(self):
        session = _make_session_with_deck()
        session.decklist.enable_background()
        session.decklist.add_card("Cloakwood Hermit", "Commander")
        session.decklist.add_card("Criminal Past", "Commander")
        handle_decklist_disable_background(session, self._cmd())
        assert session.decklist.categories["commander"].cards == []
        assert "Cloakwood Hermit" in session.decklist.categories["uncategorized"].cards

    def test_returns_confirmation_message(self):
        session = _make_session_with_deck()
        session.decklist.enable_background()
        result = handle_decklist_disable_background(session, self._cmd())
        assert "uncategorized" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "disable-background") in registry


class TestHandleDecklistEnableCompanion:
    """handle_decklist_enable_companion enables a separate Companion slot."""

    def _cmd(self):
        return ParsedCommand(
            kind="object_verb",
            raw="decklist enable-companion",
            obj="decklist",
            verb="enable-companion",
            args=[],
        )

    def test_no_active_decklist_returns_error(self):
        session = Session()
        result = handle_decklist_enable_companion(session, self._cmd())
        assert "No active decklist" in result

    def test_sets_companion_enabled(self):
        session = _make_session_with_deck()
        handle_decklist_enable_companion(session, self._cmd())
        assert session.decklist.companion_enabled is True

    def test_companion_category_has_one_slot(self):
        session = _make_session_with_deck()
        handle_decklist_enable_companion(session, self._cmd())
        assert session.decklist.categories["companion"].total_slots == 1

    def test_returns_confirmation_containing_companion(self):
        session = _make_session_with_deck()
        result = handle_decklist_enable_companion(session, self._cmd())
        assert "companion" in result.lower()
        assert "card add" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "enable-companion") in registry


class TestHandleDecklistDisableCompanion:
    """handle_decklist_disable_companion removes the Companion slot."""

    def _cmd(self):
        return ParsedCommand(
            kind="object_verb",
            raw="decklist disable-companion",
            obj="decklist",
            verb="disable-companion",
            args=[],
        )

    def test_no_active_decklist_returns_error(self):
        session = Session()
        result = handle_decklist_disable_companion(session, self._cmd())
        assert "No active decklist" in result

    def test_clears_companion_enabled(self):
        session = _make_session_with_deck()
        session.decklist.enable_companion()
        handle_decklist_disable_companion(session, self._cmd())
        assert session.decklist.companion_enabled is False

    def test_companion_card_moves_to_uncategorized(self):
        session = _make_session_with_deck()
        session.decklist.enable_companion()
        session.decklist.add_card("Lurrus of the Dream-Den", "Companion")
        handle_decklist_disable_companion(session, self._cmd())
        assert "companion" not in session.decklist.categories
        assert (
            "Lurrus of the Dream-Den"
            in session.decklist.categories["uncategorized"].cards
        )

    def test_returns_confirmation_containing_companion_and_uncategorized(self):
        session = _make_session_with_deck()
        session.decklist.enable_companion()
        result = handle_decklist_disable_companion(session, self._cmd())
        assert "companion" in result.lower()
        assert "uncategorized" in result.lower()

    def test_registered_in_dispatch_table(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "disable-companion") in registry


class TestDispatchedHandlerProtocol:
    def test_dispatched_handler_protocol_is_importable(self):
        from deckslots.commands import DispatchedHandler  # noqa: F401


def _cmd(obj, verb, *args):
    return ParsedCommand(
        kind="object_verb",
        raw=f"{obj} {verb} {' '.join(args)}",
        obj=obj,
        verb=verb,
        args=list(args),
    )


class TestHandleTemplateList:
    def test_no_active_deck_still_works(self):
        session = Session()
        result = handle_template_list(session, _cmd("template", "list"))
        assert "Goldfish Fundamentals" in result

    def test_shows_builtin_label(self):
        session = Session()
        result = handle_template_list(session, _cmd("template", "list"))
        assert "[built-in]" in result

    def test_shows_user_label(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        user_dir = tmp_path / "deckslots" / "templates"
        user_dir.mkdir(parents=True)
        (user_dir / "custom.tmpl").write_text("# Custom\nRamp [5 slots]\n")
        session = Session()
        result = handle_template_list(session, _cmd("template", "list"))
        assert "[user]" in result
        assert "Custom" in result

    def test_shows_category_summary(self):
        session = Session()
        result = handle_template_list(session, _cmd("template", "list"))
        # category summary shows slot counts in parentheses, e.g. "Ramp (10)"
        assert "Ramp (10)" in result


class TestHandleTemplateSave:
    def test_no_active_deck_returns_error(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        session = Session()
        save_cmd = _cmd("template", "save", "My", "Template")
        result = handle_template_save(session, save_cmd)
        assert "No active decklist" in result

    def test_saves_user_categories_as_template(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        save_cmd = _cmd("template", "save", "My", "Template")
        result = handle_template_save(session, save_cmd)
        assert "Saved template" in result
        assert "My Template" in result

    def test_saved_template_excludes_fixed_categories(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        session = _make_session_with_deck()
        session.decklist.add_category("Ramp", 10)
        handle_template_save(session, _cmd("template", "save", "Fixed", "Check"))
        user_dir = tmp_path / "deckslots" / "templates"
        content = (user_dir / "fixed-check.tmpl").read_text()
        assert "Commander" not in content
        assert "Basic Lands" not in content
        assert "Ramp" in content

    def test_no_name_returns_usage(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        session = _make_session_with_deck()
        result = handle_template_save(session, _cmd("template", "save"))
        assert "Usage" in result


class TestValidateTemplateSave:
    def test_no_active_deck_returns_error(self):
        session = Session()
        error = validate_template_save(session, "Any Name")
        assert error is not None

    def test_empty_name_returns_error(self):
        session = _make_session_with_deck()
        error = validate_template_save(session, "")
        assert error is not None

    def test_valid_session_and_name_returns_none(self):
        session = _make_session_with_deck()
        error = validate_template_save(session, "My Template")
        assert error is None


class TestHandleDecklistApplyTemplate:
    def test_applies_known_template(self):
        session = _make_session_with_deck()
        result = handle_decklist_apply_template(
            session, _cmd("decklist", "apply-template", "Goldfish", "Fundamentals")
        )
        assert "Applied template" in result
        assert "Goldfish Fundamentals" in result

    def test_creates_template_categories_in_deck(self):
        session = _make_session_with_deck()
        handle_decklist_apply_template(
            session, _cmd("decklist", "apply-template", "Goldfish", "Fundamentals")
        )
        assert "ramp" in session.decklist.categories

    def test_unknown_template_returns_error(self):
        session = _make_session_with_deck()
        result = handle_decklist_apply_template(
            session, _cmd("decklist", "apply-template", "Nonexistent", "XYZ")
        )
        assert "not found" in result.lower() or "unknown" in result.lower()

    def test_no_active_deck_returns_error(self):
        session = Session()
        result = handle_decklist_apply_template(
            session, _cmd("decklist", "apply-template", "Goldfish", "Fundamentals")
        )
        assert "No active decklist" in result

    def test_reports_moved_card_count(self):
        session = _make_session_with_deck()
        session.decklist.add_category("Old", 5)
        session.decklist.add_card("Sol Ring", "Old")
        result = handle_decklist_apply_template(
            session, _cmd("decklist", "apply-template", "Goldfish", "Fundamentals")
        )
        assert "1 card(s) moved" in result

    def test_no_args_returns_usage(self):
        session = _make_session_with_deck()
        result = handle_decklist_apply_template(
            session, _cmd("decklist", "apply-template")
        )
        assert "Usage" in result


class TestHandleDecklistCreateWithTemplate:
    def _gf_cmd(self):
        return _cmd(
            "decklist", "create", "MyDeck", "--template", "Goldfish", "Fundamentals"
        )

    def test_create_with_valid_template(self):
        session = Session()
        result = handle_decklist_create(session, self._gf_cmd())
        assert "MyDeck" in result
        assert "Goldfish Fundamentals" in result

    def test_template_categories_applied_to_new_deck(self):
        session = Session()
        handle_decklist_create(session, self._gf_cmd())
        assert "ramp" in session.decklist.categories

    def test_unknown_template_returns_error_without_creating(self):
        session = Session()
        cmd = _cmd("decklist", "create", "MyDeck", "--template", "NoSuchTemplate")
        result = handle_decklist_create(session, cmd)
        assert "not found" in result.lower() or "unknown" in result.lower()
        assert session.decklist is None

    def test_create_without_template_unchanged(self):
        session = Session()
        cmd = _cmd("decklist", "create", "MyDeck")
        result = handle_decklist_create(session, cmd)
        assert "Created decklist 'MyDeck'" in result
        assert session.decklist is not None


class TestHandleTemplateExport:
    def test_exports_known_template_to_file(self, tmp_path):
        session = Session()
        filepath = str(tmp_path / "out.tmpl")
        result = handle_template_export(
            session, _cmd("template", "export", "Goldfish", "Fundamentals", filepath)
        )
        assert "Exported" in result
        assert (tmp_path / "out.tmpl").exists()

    def test_exported_file_is_parseable(self, tmp_path):
        from deckslots.templates import _parse_template_content

        session = Session()
        filepath = str(tmp_path / "out.tmpl")
        handle_template_export(
            session, _cmd("template", "export", "Goldfish", "Fundamentals", filepath)
        )
        content = (tmp_path / "out.tmpl").read_text()
        t = _parse_template_content(content)
        assert t.name == "Goldfish Fundamentals"

    def test_unknown_template_returns_error(self, tmp_path):
        session = Session()
        filepath = str(tmp_path / "out.tmpl")
        result = handle_template_export(
            session, _cmd("template", "export", "NoSuchTemplate", filepath)
        )
        assert "not found" in result.lower() or "unknown" in result.lower()

    def test_no_args_returns_usage(self):
        session = Session()
        result = handle_template_export(session, _cmd("template", "export"))
        assert "Usage" in result


class TestHandleTemplateImport:
    def test_imports_template_from_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        src = tmp_path / "src.tmpl"
        src.write_text("# New Template\nRamp [10 slots]\n")
        session = Session()
        result = handle_template_import(session, _cmd("template", "import", str(src)))
        assert "Imported" in result
        assert "New Template" in result

    def test_imported_template_is_findable(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        src = tmp_path / "src.tmpl"
        src.write_text("# Imported One\nRamp [5 slots]\n")
        session = Session()
        handle_template_import(session, _cmd("template", "import", str(src)))
        from deckslots.templates import find_template

        t = find_template("Imported One")
        assert t is not None

    def test_nonexistent_file_returns_error(self):
        session = Session()
        result = handle_template_import(
            session, _cmd("template", "import", "/nonexistent/path.tmpl")
        )
        assert "not found" in result.lower() or "error" in result.lower()

    def test_no_args_returns_usage(self):
        session = Session()
        result = handle_template_import(session, _cmd("template", "import"))
        assert "Usage" in result


class TestTemplateHandlersInRegistry:
    def test_template_list_registered(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("template", "list") in registry

    def test_template_save_registered(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("template", "save") in registry

    def test_template_export_registered(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("template", "export") in registry

    def test_template_import_registered(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("template", "import") in registry

    def test_decklist_apply_template_registered(self):
        session = _make_session_with_deck()
        registry = register_all_handlers(session)
        assert ("decklist", "apply-template") in registry


class TestHelpIncludesTemplateCommands:
    def test_help_mentions_template_list(self):
        assert "template list" in handle_help()

    def test_help_mentions_template_save(self):
        assert "template save" in handle_help()

    def test_help_mentions_template_export(self):
        assert "template export" in handle_help()

    def test_help_mentions_template_import(self):
        assert "template import" in handle_help()

    def test_help_mentions_decklist_apply_template(self):
        assert "decklist apply-template" in handle_help()


class TestCommandsLogging:
    """commands.py logs key domain events."""

    def test_card_add_logs_debug(self, caplog):
        import logging

        from deckslots.cli import ParsedCommand
        from deckslots.commands import (
            Session,
            handle_card_add,
            handle_decklist_create,
        )

        def _make_cmd(raw, obj, verb, args):
            return ParsedCommand(kind="object_verb", raw=raw, obj=obj, verb=verb, args=args)

        session = Session()
        handle_decklist_create(session, _make_cmd("decklist create Test", "decklist", "create", ["Test"]))
        with caplog.at_level(logging.DEBUG, logger="deckslots.commands"):
            handle_card_add(session, _make_cmd("card add Commander Sol Ring", "card", "add", ["Commander", "Sol", "Ring"]))
        assert any("Sol Ring" in r.message for r in caplog.records)

    def test_save_logs_debug(self, caplog, tmp_path, monkeypatch):
        import logging

        from deckslots.cli import ParsedCommand
        from deckslots.commands import (
            Session,
            handle_decklist_create,
            handle_decklist_save,
        )

        def _make_cmd(raw, obj, verb, args):
            return ParsedCommand(kind="object_verb", raw=raw, obj=obj, verb=verb, args=args)

        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        session = Session()
        handle_decklist_create(session, _make_cmd("decklist create Test", "decklist", "create", ["Test"]))
        with caplog.at_level(logging.DEBUG, logger="deckslots.commands"):
            handle_decklist_save(session, _make_cmd("decklist save", "decklist", "save", []))
        assert any("saved" in r.message.lower() for r in caplog.records)


# ---------------------------------------------------------------------------
# Scryfall validation integration (US-012)
# ---------------------------------------------------------------------------

_SMALL_INDEX = {
    "sol ring": {"name": "Sol Ring", "legalities": {"commander": "legal"}},
    "oko, thief of crowns": {
        "name": "Oko, Thief of Crowns",
        "legalities": {"commander": "banned"},
    },
}


def _make_session_with_index():
    """Session with an active deck and a small Scryfall index loaded."""
    session = _make_session_with_deck()
    session.scryfall_index = _SMALL_INDEX
    return session


def _card_add_cmd(category, *card_parts):
    args = [category] + list(card_parts)
    raw = "card add " + " ".join(args)
    return ParsedCommand(kind="object_verb", raw=raw, obj="card", verb="add", args=args)


class TestScryfallValidationInCardAdd:
    def test_no_warning_for_valid_legal_card(self):
        session = _make_session_with_index()
        session.decklist.add_category("Ramp", 10)
        result = handle_card_add(session, _card_add_cmd("Ramp", "Sol", "Ring"))
        assert "Warning" not in result

    def test_warns_when_card_not_in_index(self):
        session = _make_session_with_index()
        session.decklist.add_category("Ramp", 10)
        result = handle_card_add(
            session, _card_add_cmd("Ramp", "Gibberish", "Cardname")
        )
        assert "Warning" in result
        assert "not found" in result.lower()

    def test_warns_when_card_not_commander_legal(self):
        session = _make_session_with_index()
        session.decklist.add_category("Walkers", 10)
        result = handle_card_add(
            session, _card_add_cmd("Walkers", "Oko,", "Thief", "of", "Crowns")
        )
        assert "Warning" in result
        assert "not legal" in result.lower() or "banned" in result.lower()

    def test_card_still_added_despite_legality_warning(self):
        session = _make_session_with_index()
        session.decklist.add_category("Walkers", 10)
        handle_card_add(
            session, _card_add_cmd("Walkers", "Oko,", "Thief", "of", "Crowns")
        )
        assert "Oko, Thief of Crowns" in session.decklist.categories["walkers"].cards

    def test_no_validation_when_index_is_none(self):
        session = _make_session_with_deck()
        session.scryfall_index = None
        session.decklist.add_category("Ramp", 10)
        # Even a card that would fail validation proceeds silently
        result = handle_card_add(
            session, _card_add_cmd("Ramp", "Gibberish", "Cardname")
        )
        # No deck error, no warning — card added
        assert "Warning" not in result

    def test_basic_lands_skip_validation(self):
        session = _make_session_with_index()
        result = handle_card_add(session, _card_add_cmd("Basic", "Lands", "Forest"))
        assert "Warning" not in result


class TestSessionHasScryfallIndex:
    def test_session_starts_with_no_index(self):
        session = Session()
        assert session.scryfall_index is None
