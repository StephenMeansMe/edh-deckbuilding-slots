"""CliRunner-based functional tests replacing scrut tests in tests/functional/.

These tests use click.testing.CliRunner to invoke the REPL in-process,
avoiding the need for the scrut binary or subprocess spawning.  This makes
the suite runnable in any environment that has the Python dependencies
installed, including cloud-based Claude Code deployments.

Coverage maps to scrut files:
  01-startup.md     → TestStartup
  02-decklist.md    → TestDecklist
  03-categories.md  → TestCategories
  04-cards.md       → TestCards
  05-uncategorized.md → TestUncategorized
  09-consistency.md → TestConsistency
  10-rename.md      → TestRename
  11-partners.md    → TestPartners
  12-background.md  → TestBackground
  13-companion.md   → TestCompanion
  14-templates.md   → TestTemplates
  15-validation.md  → TestValidation
"""

import json
from pathlib import Path

from click.testing import CliRunner

from deckslots.cli import main

# Fixture files used by import/move/delete tests (mirrors $TESTDIR in scrut).
TESTDIR = Path(__file__).parent / "functional"
DECK_TXT = TESTDIR / "deck.txt"
DOUBLE_TXT = TESTDIR / "double.txt"


def _run(
    commands: str,
    state_home: Path,
    data_home: Path | None = None,
    cache_home: Path | None = None,
    config_home: Path | None = None,
) -> str:
    """Invoke the deckslots REPL in-process and return captured stdout."""
    env: dict[str, str] = {"XDG_STATE_HOME": str(state_home)}
    if data_home is not None:
        env["XDG_DATA_HOME"] = str(data_home)
    if cache_home is not None:
        env["XDG_CACHE_HOME"] = str(cache_home)
    if config_home is not None:
        env["XDG_CONFIG_HOME"] = str(config_home)
    runner = CliRunner(env=env)
    result = runner.invoke(main, input=commands)
    return result.output


# ---------------------------------------------------------------------------
# 01-startup.md
# ---------------------------------------------------------------------------


class TestStartup:
    def test_eof_exits_cleanly(self, tmp_path):
        out = _run("", tmp_path)
        assert out == "deckslots> Welcome to deckslots.\ndeckslots> Goodbye.\n"

    def test_quit_exits_cleanly(self, tmp_path):
        out = _run("quit\n", tmp_path)
        assert out == "deckslots> Welcome to deckslots.\ndeckslots> Goodbye.\n"

    def test_exit_exits_cleanly(self, tmp_path):
        out = _run("exit\n", tmp_path)
        assert out == "deckslots> Welcome to deckslots.\ndeckslots> Goodbye.\n"

    def test_quit_does_not_print_unknown_command_error(self, tmp_path):
        out = _run("quit\n", tmp_path)
        assert "Unknown command" not in out

    def test_unknown_command_echoes_rejected_input(self, tmp_path):
        out = _run("cast lightning bolt\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Unknown command: cast lightning bolt\n"
            "deckslots> Goodbye.\n"
        )

    def test_multiple_unknown_commands_each_rejected(self, tmp_path):
        out = _run("foo\nbar\nbaz\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Unknown command: foo\n"
            "deckslots> Unknown command: bar\n"
            "deckslots> Unknown command: baz\n"
            "deckslots> Goodbye.\n"
        )

    def test_help_shows_all_available_commands(self, tmp_path):
        out = _run("help\nquit\n", tmp_path)
        assert "deckslots> Available commands:" in out
        # Spot-check a representative cross-section of the help table.
        assert "decklist create <name>" in out
        assert "category create <n> <s>" in out
        assert "card add <cat> <name>" in out
        assert "card move <name> <cat>" in out
        assert "template list" in out
        assert "quit / exit" in out


# ---------------------------------------------------------------------------
# 02-decklist.md
# ---------------------------------------------------------------------------


class TestDecklist:
    def test_create_prints_confirmation(self, tmp_path):
        out = _run("decklist create TestDeck\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_show_displays_name_and_category_summary(self, tmp_path):
        out = _run("decklist create TestDeck\ndecklist show\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Decklist: TestDeck\n"
            "Total slots: 1 (0 filled)\n"
            "Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "TestDeck (0/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_create_without_name_shows_usage_error(self, tmp_path):
        out = _run("decklist create\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Usage: decklist create <name>\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_show_without_active_decklist_shows_error(self, tmp_path):
        out = _run("decklist show\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# 03-categories.md
# ---------------------------------------------------------------------------


class TestCategories:
    def test_create_prints_confirmation(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\nquit\n", tmp_path
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_create_without_active_decklist_shows_error(self, tmp_path):
        out = _run("category create Ramp 10\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_list_shows_all_categories_including_user_created(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\ncategory list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Ramp: 0/10 slots filled\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# 04-cards.md
# ---------------------------------------------------------------------------


class TestCards:
    def test_card_add_to_named_category(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Ramp Sol Ring\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Added 'Sol Ring' to 'Ramp'.\n"
            "TestDeck (1/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_add_to_basic_lands_multi_word_category(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncard add Basic Lands Forest\nquit\n", tmp_path
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Added 'Forest' to 'Basic Lands'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_add_without_active_decklist_shows_error(self, tmp_path):
        out = _run("card add Ramp Sol Ring\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_move_reports_source_and_destination(self, tmp_path):
        out = _run(
            f"decklist import {DECK_TXT}\ncategory create Ramp 10\n"
            "card move Sol Ring Ramp\nquit\n",
            tmp_path,
        )
        assert "Moved 'Sol Ring' from 'Uncategorized' to 'Ramp'." in out

    def test_card_move_error_card_not_found(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card move Nonexistent Ramp\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Card 'Nonexistent' not found in the decklist.\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_move_error_category_not_found(self, tmp_path):
        out = _run(
            f"decklist import {DECK_TXT}\ncard move Sol Ring NoSuchCategory\nquit\n",
            tmp_path,
        )
        assert "Category not found." in out

    def test_card_move_without_active_decklist_shows_error(self, tmp_path):
        out = _run("card move Sol Ring Ramp\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_remove_moves_to_uncategorized(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Ramp Sol Ring\ncard remove Sol Ring\nquit\n",
            tmp_path,
        )
        assert "Removed 'Sol Ring' from 'Ramp'. Card is now in Uncategorized." in out

    def test_card_remove_error_card_not_found(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncard remove Nonexistent\nquit\n", tmp_path
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Card 'Nonexistent' not found in the decklist.\n"
            "TestDeck (0/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_remove_without_active_decklist_shows_error(self, tmp_path):
        out = _run("card remove Sol Ring\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_delete_permanently_removes_from_category(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Ramp Sol Ring\ncard delete Sol Ring\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Added 'Sol Ring' to 'Ramp'.\n"
            "TestDeck (1/11)\n"
            "deckslots> Deleted 'Sol Ring' from the decklist.\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_delete_from_uncategorized_after_import(self, tmp_path):
        out = _run(
            f"decklist import {DECK_TXT}\ncard delete Sol Ring\nquit\n", tmp_path
        )
        assert "Deleted 'Sol Ring' from the decklist." in out

    def test_card_delete_does_not_trigger_uncategorized_warning(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Ramp Sol Ring\ncard delete Sol Ring\ncategory list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Added 'Sol Ring' to 'Ramp'.\n"
            "TestDeck (1/11)\n"
            "deckslots> Deleted 'Sol Ring' from the decklist.\n"
            "TestDeck (0/11)\n"
            "deckslots> Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Ramp: 0/10 slots filled\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_delete_without_active_decklist_shows_error(self, tmp_path):
        out = _run("card delete Sol Ring\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# 05-uncategorized.md
# ---------------------------------------------------------------------------


class TestUncategorized:
    def test_warning_appears_on_every_response_while_uncategorized_has_cards(
        self, tmp_path
    ):
        out = _run(f"decklist import {DECK_TXT}\ncategory list\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Warning: 1 card(s) in Uncategorized. "
            "Assign them to categories before finalizing your decklist.\n"
            "Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.\n"
            "deck (1/1) | Uncategorized: 1\n"
            "deckslots> Warning: 1 card(s) in Uncategorized. "
            "Assign them to categories before finalizing your decklist.\n"
            "Categories:\n"
            "  Commander: 1/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Uncategorized: 1 slots filled (uncapped)\n"
            "deck (1/1) | Uncategorized: 1\n"
            "deckslots> Goodbye.\n"
        )

    def test_no_warning_when_decklist_has_no_uncategorized_category(self, tmp_path):
        out = _run("decklist create TestDeck\ncategory list\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "TestDeck (0/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_warning_disappears_after_last_card_moved_out(self, tmp_path):
        out = _run(
            f"decklist import {DECK_TXT}\ncategory create Ramp 10\n"
            "card move Sol Ring Ramp\ncategory list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Warning: 1 card(s) in Uncategorized. "
            "Assign them to categories before finalizing your decklist.\n"
            "Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.\n"
            "deck (1/1) | Uncategorized: 1\n"
            "deckslots> Warning: 1 card(s) in Uncategorized. "
            "Assign them to categories before finalizing your decklist.\n"
            "Created category 'Ramp' with 10 slots.\n"
            "deck (1/11) | Uncategorized: 1\n"
            "deckslots> Moved 'Sol Ring' from 'Uncategorized' to 'Ramp'.\n"
            "deck (2/11)\n"
            "deckslots> Categories:\n"
            "  Commander: 1/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Uncategorized: 0 slots filled (uncapped)\n"
            "  Ramp: 1/10 slots filled\n"
            "deck (2/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_warning_disappears_after_last_card_deleted_from_uncategorized(
        self, tmp_path
    ):
        out = _run(
            f"decklist import {DECK_TXT}\ncard delete Sol Ring\ncategory list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Warning: 1 card(s) in Uncategorized. "
            "Assign them to categories before finalizing your decklist.\n"
            "Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.\n"
            "deck (1/1) | Uncategorized: 1\n"
            "deckslots> Deleted 'Sol Ring' from the decklist.\n"
            "deck (1/1)\n"
            "deckslots> Categories:\n"
            "  Commander: 1/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Uncategorized: 0 slots filled (uncapped)\n"
            "deck (1/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_remove_activates_warning_on_subsequent_commands(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Ramp Sol Ring\ncard remove Sol Ring\ncategory list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Added 'Sol Ring' to 'Ramp'.\n"
            "TestDeck (1/11)\n"
            "deckslots> Warning: 1 card(s) in Uncategorized. "
            "Assign them to categories before finalizing your decklist.\n"
            "Removed 'Sol Ring' from 'Ramp'. Card is now in Uncategorized.\n"
            "TestDeck (0/11) | Uncategorized: 1\n"
            "deckslots> Warning: 1 card(s) in Uncategorized. "
            "Assign them to categories before finalizing your decklist.\n"
            "Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Ramp: 0/10 slots filled\n"
            "  Uncategorized: 1 slots filled (uncapped)\n"
            "TestDeck (0/11) | Uncategorized: 1\n"
            "deckslots> Goodbye.\n"
        )

    def test_uncategorized_warning_is_styled_in_color_mode(self, tmp_path):
        """In colour-capable terminals the Uncategorized warning should carry
        ANSI escape codes so it stands out from normal command output."""
        runner = CliRunner(env={"XDG_STATE_HOME": str(tmp_path)})
        result = runner.invoke(
            main,
            input=(
                f"decklist import {DECK_TXT}\n"  # Sol Ring lands in Uncategorized
                "quit\n"
            ),
            color=True,
        )
        assert "\033[" in result.output  # ANSI escape present → styled


# ---------------------------------------------------------------------------
# 09-consistency.md
# ---------------------------------------------------------------------------


class TestConsistency:
    def test_card_move_to_same_category_is_noop(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Ramp Sol Ring\ncard move Sol Ring Ramp\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Added 'Sol Ring' to 'Ramp'.\n"
            "TestDeck (1/11)\n"
            "deckslots> 'Sol Ring' is already in 'Ramp'. Nothing to do.\n"
            "TestDeck (1/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_add_rejects_basic_land_in_non_basic_lands_category(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Ramp Forest\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Error: Basic lands can only be added to the 'Basic Lands' category.\n"  # noqa: E501
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_move_rejects_basic_land_to_non_basic_lands_category(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "card add Basic Lands Forest\ncard move Forest Ramp\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> Added 'Forest' to 'Basic Lands'.\n"
            "TestDeck (0/11)\n"
            "deckslots> Error: Basic lands can only be added to the 'Basic Lands' category.\n"  # noqa: E501
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_card_move_enforces_singleton_rule(self, tmp_path):
        out = _run(
            f"decklist import {DOUBLE_TXT}\ncategory create Ramp 10\n"
            "category create Draw 10\ncard move Sol Ring Ramp\n"
            "card move Sol Ring Draw\nquit\n",
            tmp_path,
        )
        assert "Moved 'Sol Ring' from 'Uncategorized' to 'Ramp'." in out
        assert "Error: 'Sol Ring' is already in the deck (in 'Ramp')." in out


# ---------------------------------------------------------------------------
# 10-rename.md
# ---------------------------------------------------------------------------


class TestRename:
    def test_decklist_rename_prompts_and_applies_new_name(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ndecklist rename\nMy Commander Deck\n"
            "decklist show\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> New name: Renamed decklist to 'My Commander Deck'.\n"
            "My Commander Deck (0/1)\n"
            "deckslots> Decklist: My Commander Deck\n"
            "Total slots: 1 (0 filled)\n"
            "Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "My Commander Deck (0/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_decklist_rename_without_active_decklist_shows_error(self, tmp_path):
        out = _run("decklist rename\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "deckslots> Goodbye.\n"
        )

    def test_category_rename_prompts_and_applies_new_name(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "category rename Ramp\nMana Rocks\ncategory list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> New name: Renamed category 'Ramp' to 'Mana Rocks'.\n"
            "TestDeck (0/11)\n"
            "deckslots> Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Mana Rocks: 0/10 slots filled\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_category_rename_with_multi_word_category_name(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Mana Ramp 10\n"
            "category rename Mana Ramp\nAcceleration Package\ncategory list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Mana Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> New name: Renamed category 'Mana Ramp' to 'Acceleration Package'.\n"  # noqa: E501
            "TestDeck (0/11)\n"
            "deckslots> Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Acceleration Package: 0/10 slots filled\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_category_rename_fixed_category_shows_error_without_prompting(
        self, tmp_path
    ):
        out = _run(
            "decklist create TestDeck\ncategory rename commander\nquit\n", tmp_path
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Cannot rename fixed category 'Commander'.\n"
            "deckslots> Goodbye.\n"
        )

    def test_category_rename_nonexistent_category_shows_error_without_prompting(
        self, tmp_path
    ):
        out = _run(
            "decklist create TestDeck\ncategory rename nonexistent\nquit\n", tmp_path
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Category 'nonexistent' not found.\n"
            "deckslots> Goodbye.\n"
        )

    def test_category_rename_without_args_shows_usage(self, tmp_path):
        out = _run("decklist create TestDeck\ncategory rename\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Usage: category rename <name>\n"
            "deckslots> Goodbye.\n"
        )

    def test_rename_persists_through_save_and_load(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "category rename Ramp\nMana Rocks\ndecklist save\ndecklist load\n"
            "category list\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "TestDeck (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "TestDeck (0/11)\n"
            "deckslots> New name: Renamed category 'Ramp' to 'Mana Rocks'.\n"
            "TestDeck (0/11)\n"
            "deckslots> Saved 'TestDeck'.\n"
            "TestDeck (0/11)\n"
            "deckslots> Loaded 'TestDeck'.\n"
            "TestDeck (0/11)\n"
            "deckslots> Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Mana Rocks: 0/10 slots filled\n"
            "TestDeck (0/11)\n"
            "deckslots> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# 11-partners.md
# ---------------------------------------------------------------------------


class TestPartners:
    def test_enable_partners_allows_two_commanders(self, tmp_path):
        out = _run(
            "decklist create PartnerDeck\ndecklist enable-partners\n"
            "card add Commander Malcolm, Keen-Eyed Navigator\n"
            "card add Commander Tana, the Bloodsower\ndecklist show\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'PartnerDeck'.\n"
            "PartnerDeck (0/1)\n"
            "deckslots> Partners mode enabled. The Commander category now has 2 slots.\n"  # noqa: E501
            "PartnerDeck (0/2)\n"
            "deckslots> Added 'Malcolm, Keen-Eyed Navigator' to 'Commander'.\n"
            "PartnerDeck (1/2)\n"
            "deckslots> Added 'Tana, the Bloodsower' to 'Commander'.\n"
            "PartnerDeck (2/2)\n"
            "deckslots> Decklist: PartnerDeck\n"
            "Total slots: 2 (2 filled)\n"
            "Categories:\n"
            "  Commander: 2/2 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "PartnerDeck (2/2)\n"
            "deckslots> Goodbye.\n"
        )

    def test_enable_partners_without_active_decklist_shows_error(self, tmp_path):
        out = _run("decklist enable-partners\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_partners_mode_survives_save_and_load_round_trip(self, tmp_path):
        state_home = tmp_path / "state"
        # Session 1: save with partners + two commanders
        out1 = _run(
            "decklist create PartnerDeck\ndecklist enable-partners\n"
            "card add Commander Malcolm, Keen-Eyed Navigator\n"
            "card add Commander Tana, the Bloodsower\ndecklist save\nquit\n",
            state_home,
        )
        assert "Saved 'PartnerDeck'." in out1
        # Session 2: autoload and show
        out2 = _run("decklist show\nquit\n", state_home)
        assert "Resumed 'PartnerDeck'." in out2
        # Save format does not preserve mode flags, so overcrowded warning fires.
        assert "Warning: Commander has more cards than enabled modes allow." in out2
        assert "Commander: 2/2 slots filled" in out2


# ---------------------------------------------------------------------------
# 12-background.md
# ---------------------------------------------------------------------------


class TestBackground:
    def test_enable_background_allows_two_commanders(self, tmp_path):
        out = _run(
            "decklist create BgDeck\ndecklist enable-background\n"
            "card add Commander Cloakwood Hermit\n"
            "card add Commander Criminal Past\ndecklist show\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'BgDeck'.\n"
            "BgDeck (0/1)\n"
            "deckslots> Background mode enabled. The Commander category now has 2 slots.\n"  # noqa: E501
            "BgDeck (0/2)\n"
            "deckslots> Added 'Cloakwood Hermit' to 'Commander'.\n"
            "BgDeck (1/2)\n"
            "deckslots> Added 'Criminal Past' to 'Commander'.\n"
            "BgDeck (2/2)\n"
            "deckslots> Decklist: BgDeck\n"
            "Total slots: 2 (2 filled)\n"
            "Categories:\n"
            "  Commander: 2/2 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "BgDeck (2/2)\n"
            "deckslots> Goodbye.\n"
        )

    def test_enable_background_without_active_decklist_shows_error(self, tmp_path):
        out = _run("decklist enable-background\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_disable_partners_moves_all_commanders_to_uncategorized(self, tmp_path):
        out = _run(
            "decklist create PartnerDeck\ndecklist enable-partners\n"
            "card add Commander Malcolm, Keen-Eyed Navigator\n"
            "card add Commander Tana, the Bloodsower\n"
            "decklist disable-partners\ndecklist show\nquit\n",
            tmp_path,
        )
        assert "Partners mode disabled. All commanders moved to Uncategorized." in out
        assert "Commander: 0/1 slots filled" in out
        assert "Uncategorized: 2 slots filled (uncapped)" in out

    def test_both_modes_enabled_gives_three_commander_slots(self, tmp_path):
        out = _run(
            "decklist create Hybrid\ndecklist enable-partners\n"
            "decklist enable-background\ndecklist show\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'Hybrid'.\n"
            "Hybrid (0/1)\n"
            "deckslots> Partners mode enabled. The Commander category now has 2 slots.\n"  # noqa: E501
            "Hybrid (0/2)\n"
            "deckslots> Background mode enabled. The Commander category now has 3 slots.\n"  # noqa: E501
            "Hybrid (0/3)\n"
            "deckslots> Decklist: Hybrid\n"
            "Total slots: 3 (0 filled)\n"
            "Categories:\n"
            "  Commander: 0/3 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "Hybrid (0/3)\n"
            "deckslots> Goodbye.\n"
        )

    def test_overcrowded_warning_fires_after_loading_save_with_no_mode(self, tmp_path):
        state_home = tmp_path / "state"
        _run(
            "decklist create BgDeck\ndecklist enable-background\n"
            "card add Commander Cloakwood Hermit\n"
            "card add Commander Criminal Past\ndecklist save\nquit\n",
            state_home,
        )
        out2 = _run("decklist show\nquit\n", state_home)
        assert "Resumed 'BgDeck'." in out2
        assert "Warning: Commander has more cards than enabled modes allow." in out2
        assert "Commander: 2/2 slots filled" in out2


# ---------------------------------------------------------------------------
# 13-companion.md
# ---------------------------------------------------------------------------


class TestCompanion:
    def test_enable_companion_shows_companion_category_in_show(self, tmp_path):
        out = _run(
            "decklist create LurrusDeck\ndecklist enable-companion\ndecklist show\nquit\n",  # noqa: E501
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'LurrusDeck'.\n"
            "LurrusDeck (0/1)\n"
            "deckslots> Companion slot enabled. "
            "Add a companion with 'card add Companion <card name>'.\n"
            "LurrusDeck (0/2) | Companion: empty\n"
            "deckslots> Warning: Companion slot is empty. "
            "Add a companion with 'card add Companion <card name>'.\n"
            "Decklist: LurrusDeck\n"
            "Total slots: 2 (0 filled)\n"
            "Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Companion: 0/1 slots filled\n"
            "LurrusDeck (0/2) | Companion: empty\n"
            "deckslots> Goodbye.\n"
        )

    def test_enable_companion_without_active_decklist_shows_error(self, tmp_path):
        out = _run("decklist enable-companion\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "No active decklist\n"
            "deckslots> Goodbye.\n"
        )

    def test_disable_companion_moves_card_to_uncategorized(self, tmp_path):
        out = _run(
            "decklist create LurrusDeck\ndecklist enable-companion\n"
            "card add Companion Lurrus of the Dream-Den\n"
            "decklist disable-companion\ndecklist show\nquit\n",
            tmp_path,
        )
        assert (
            "Companion mode disabled. All companion cards moved to Uncategorized."
            in out
        )
        assert "Uncategorized: 1 slots filled (uncapped)" in out

    def test_save_and_load_round_trip_preserves_companion_card(self, tmp_path):
        state_home = tmp_path / "state"
        _run(
            "decklist create LurrusDeck\ndecklist enable-companion\n"
            "card add Companion Lurrus of the Dream-Den\ndecklist save\nquit\n",
            state_home,
        )
        out2 = _run("decklist show\nquit\n", state_home)
        assert "Resumed 'LurrusDeck'." in out2
        assert "Companion: 1/1 slots filled" in out2

    def test_export_writes_companion_section(self, tmp_path):
        export_path = tmp_path / "export.txt"
        _run(
            "decklist create LurrusDeck\ndecklist enable-companion\n"
            f"card add Companion Lurrus of the Dream-Den\n"
            f"decklist export {export_path}\nquit\n",
            tmp_path,
        )
        content = export_path.read_text()
        assert "Companion\n1 Lurrus of the Dream-Den" in content
        assert content.index("Companion") < content.index("Maindeck")

    def test_export_import_round_trip_restores_companion_mode(self, tmp_path):
        export_path = tmp_path / "round-trip.txt"
        state1 = tmp_path / "state1"
        state2 = tmp_path / "state2"
        _run(
            "decklist create LurrusDeck\ndecklist enable-companion\n"
            f"card add Companion Lurrus of the Dream-Den\n"
            f"decklist export {export_path}\nquit\n",
            state1,
        )
        out2 = _run(f"decklist import {export_path}\ndecklist show\nquit\n", state2)
        assert "Companion: 1/1 slots filled" in out2


# ---------------------------------------------------------------------------
# 14-templates.md
# ---------------------------------------------------------------------------


class TestTemplates:
    def test_template_list_shows_builtin_templates(self, tmp_path):
        out = _run("template list\nquit\n", tmp_path, data_home=tmp_path / "data")
        assert "Goldfish Fundamentals" in out
        assert "[built-in]" in out

    def test_template_list_without_active_deck_still_works(self, tmp_path):
        out = _run("template list\nquit\n", tmp_path, data_home=tmp_path / "data")
        assert "Templates:" in out
        assert "Goldfish Fundamentals" in out

    def test_decklist_create_with_valid_template_applies_categories(self, tmp_path):
        out = _run(
            "decklist create Aristocrats --template Goldfish Fundamentals\n"
            "decklist show\nquit\n",
            tmp_path,
            data_home=tmp_path / "data",
        )
        assert (
            "Created decklist 'Aristocrats' with template 'Goldfish Fundamentals'."
            in out
        )  # noqa: E501
        assert "Ramp: 0/10 slots filled" in out
        assert "Card Advantage: 0/10 slots filled" in out

    def test_decklist_create_with_unknown_template_returns_error(self, tmp_path):
        out = _run(
            "decklist create MyDeck --template NoSuchTemplate\ndecklist show\nquit\n",
            tmp_path,
            data_home=tmp_path / "data",
        )
        assert "Template 'NoSuchTemplate' not found." in out
        assert "No active decklist." in out

    def test_decklist_apply_template_applies_categories_and_moves_cards(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Old 5\ncard add Old Sol Ring\n"
            "decklist apply-template Goldfish Fundamentals\nquit\n",
            tmp_path,
            data_home=tmp_path / "data",
        )
        assert "Applied template 'Goldfish Fundamentals' to 'TestDeck'." in out
        assert "1 card(s) moved to Uncategorized." in out

    def test_decklist_apply_template_with_unknown_template_returns_error(
        self, tmp_path
    ):
        out = _run(
            "decklist create TestDeck\ndecklist apply-template NoSuchTemplate\nquit\n",
            tmp_path,
            data_home=tmp_path / "data",
        )
        assert "Template 'NoSuchTemplate' not found." in out

    def test_decklist_apply_template_without_active_deck_returns_error(self, tmp_path):
        out = _run(
            "decklist apply-template Goldfish Fundamentals\nquit\n",
            tmp_path,
            data_home=tmp_path / "data",
        )
        assert "No active decklist." in out

    def test_template_save_stores_current_categories(self, tmp_path):
        data_home = tmp_path / "data2"
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "category create Draw 8\ntemplate save My Custom\ntemplate list\nquit\n",
            tmp_path,
            data_home=data_home,
        )
        assert "Saved template 'My Custom'." in out
        assert "[user] My Custom" in out

    def test_template_save_without_active_deck_returns_error(self, tmp_path):
        out = _run(
            "template save My Template\nquit\n",
            tmp_path,
            data_home=tmp_path / "data",
        )
        assert "No active decklist." in out

    def test_template_export_writes_template_file(self, tmp_path):
        data_home = tmp_path / "data3"
        export_path = tmp_path / "exported.tmpl"
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            f"template save ExportMe\ntemplate export ExportMe {export_path}\nquit\n",
            tmp_path,
            data_home=data_home,
        )
        assert "Saved template 'ExportMe'." in out
        assert export_path.exists()

    def test_template_import_loads_template_from_file(self, tmp_path):
        import_path = tmp_path / "imp.tmpl"
        import_path.write_text("# Imported Template\nRamp [12 slots]\n")
        data_home = tmp_path / "data4"
        out = _run(
            f"template import {import_path}\ntemplate list\nquit\n",
            tmp_path,
            data_home=data_home,
        )
        assert "Imported template 'Imported Template'." in out
        assert "[user] Imported Template" in out

    def test_template_import_with_nonexistent_file_returns_error(self, tmp_path):
        out = _run(
            "template import /nonexistent/path.tmpl\nquit\n",
            tmp_path,
            data_home=tmp_path / "data",
        )
        assert "File not found: '/nonexistent/path.tmpl'" in out

    def test_template_save_overwrite_prompt_accepts_full_word_yes(self, tmp_path):
        """The overwrite confirmation should accept the full word 'yes', not
        just the single character 'y'."""
        data_home = tmp_path / "data"
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\n"
            "template save MyTemplate\n"  # first save — no prompt
            "template save MyTemplate\n"  # second save — overwrite prompt fires
            "yes\n"  # full word; current code rejects this
            "quit\n",
            tmp_path,
            data_home=data_home,
        )
        assert "Saved template 'MyTemplate'." in out
        assert "Aborted." not in out


# ---------------------------------------------------------------------------
# 15-validation.md
# ---------------------------------------------------------------------------


def _make_scryfall_cache(cache_dir: Path) -> Path:
    """Write a minimal oracle_cards.json for validation tests."""
    cache_path = cache_dir / "deckslots"
    cache_path.mkdir(parents=True, exist_ok=True)
    (cache_path / "oracle_cards.json").write_text(
        json.dumps(
            [
                {"name": "Sol Ring", "legalities": {"commander": "legal"}},
                {
                    "name": "Oko, Thief of Crowns",
                    "legalities": {"commander": "banned"},
                },
            ]
        )
    )
    return cache_dir


class TestValidation:
    def test_legal_card_no_validation_warning(self, tmp_path):
        cache_home = _make_scryfall_cache(tmp_path / "cache")
        out = _run(
            "decklist create Test\ncategory create Ramp 10\n"
            "card add Ramp Sol Ring\nquit\n",
            tmp_path,
            cache_home=cache_home,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'Test'.\n"
            "Test (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "Test (0/11)\n"
            "deckslots> Added 'Sol Ring' to 'Ramp'.\n"
            "Test (1/11)\n"
            "deckslots> Goodbye.\n"
        )

    def test_unknown_card_shows_validation_warning(self, tmp_path):
        cache_home = _make_scryfall_cache(tmp_path / "cache")
        out = _run(
            "decklist create Test\ncategory create Ramp 10\n"
            "card add Ramp Mox Opal\nquit\n",
            tmp_path,
            cache_home=cache_home,
        )
        assert "Warning: 'Mox Opal' not found in Scryfall database." in out
        assert "Added 'Mox Opal' to 'Ramp'." in out

    def test_banned_card_shows_validation_warning(self, tmp_path):
        cache_home = _make_scryfall_cache(tmp_path / "cache")
        out = _run(
            "decklist create Test\ncategory create PW 10\n"
            "card add PW Oko, Thief of Crowns\nquit\n",
            tmp_path,
            cache_home=cache_home,
        )
        assert (
            "Warning: 'Oko, Thief of Crowns' is not legal in Commander format." in out
        )  # noqa: E501
        assert "Added 'Oko, Thief of Crowns' to 'PW'." in out

    def test_basic_lands_skip_validation(self, tmp_path):
        cache_home = _make_scryfall_cache(tmp_path / "cache")
        out = _run(
            "decklist create Test\ncard add Basic Lands Forest\nquit\n",
            tmp_path,
            cache_home=cache_home,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'Test'.\n"
            "Test (0/1)\n"
            "deckslots> Added 'Forest' to 'Basic Lands'.\n"
            "Test (0/1)\n"
            "deckslots> Goodbye.\n"
        )

    def test_no_validation_when_cache_is_absent(self, tmp_path):
        no_cache = tmp_path / "nocache"
        no_cache.mkdir()
        out = _run(
            "decklist create Test\ncategory create Ramp 10\n"
            "card add Ramp Gibberish Card\nquit\n",
            tmp_path,
            cache_home=no_cache,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'Test'.\n"
            "Test (0/1)\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "Test (0/11)\n"
            "deckslots> Added 'Gibberish Card' to 'Ramp'.\n"
            "Test (1/11)\n"
            "deckslots> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# Phase 1.5 — storage_backend config opt-in
# ---------------------------------------------------------------------------


class TestStorageBackendSelection:
    """REPL selects PlaintextRepository or SqliteRepository from config.json."""

    def _write_config(self, config_home: Path, backend: str) -> None:
        d = config_home / "deckslots"
        d.mkdir(parents=True, exist_ok=True)
        (d / "config.json").write_text(json.dumps({"storage_backend": backend}))

    def test_default_backend_writes_decklist_bak(self, tmp_path):
        state = tmp_path / "state"
        data = tmp_path / "data"
        out = _run(
            "decklist create Test\ndecklist save\nquit\n",
            state_home=state,
            data_home=data,
        )
        assert "Saved 'Test'." in out
        assert (state / "deckslots" / "decklist.bak").exists()
        assert not (data / "deckslots" / "library.db").exists()

    def test_sqlite_backend_writes_library_db(self, tmp_path):
        state = tmp_path / "state"
        data = tmp_path / "data"
        config = tmp_path / "config"
        self._write_config(config, "sqlite")
        out = _run(
            "decklist create Test\ndecklist save\nquit\n",
            state_home=state,
            data_home=data,
            config_home=config,
        )
        assert "Saved 'Test'." in out
        assert (data / "deckslots" / "library.db").exists()
        assert not (state / "deckslots" / "decklist.bak").exists()

    def test_sqlite_backend_resumes_saved_deck_across_runs(self, tmp_path):
        state = tmp_path / "state"
        data = tmp_path / "data"
        config = tmp_path / "config"
        self._write_config(config, "sqlite")
        _run(
            "decklist create Resumed\ndecklist save\nquit\n",
            state_home=state,
            data_home=data,
            config_home=config,
        )
        out2 = _run(
            "quit\n",
            state_home=state,
            data_home=data,
            config_home=config,
        )
        assert "Resumed 'Resumed'." in out2
