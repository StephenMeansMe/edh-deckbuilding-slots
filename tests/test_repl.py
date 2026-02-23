from unittest.mock import patch

from deckslots.repl import run_repl


class TestReplStartsAndRejectsInput:
    """The REPL starts, shows a prompt, and rejects all user input."""

    def test_repl_prints_prompt(self, capsys):
        """The REPL prints a prompt before reading input."""
        with patch("builtins.input", side_effect=EOFError):
            run_repl()

        output = capsys.readouterr().out
        assert "deckslots>" in output or "deckslots> " in output

    def test_repl_exits_on_eof(self):
        """The REPL exits cleanly when it receives EOF (Ctrl-D)."""
        with patch("builtins.input", side_effect=EOFError):
            run_repl()  # should not raise

    def test_repl_rejects_any_input(self, capsys):
        """The REPL prints an error for any user input."""
        user_inputs = ["hello", EOFError]
        with patch("builtins.input", side_effect=user_inputs):
            run_repl()

        output = capsys.readouterr().out
        assert "unknown command" in output.lower()

    def test_repl_rejects_multiple_inputs(self, capsys):
        """The REPL rejects every input, not just the first."""
        user_inputs = ["foo", "bar", "baz", EOFError]
        with patch("builtins.input", side_effect=user_inputs):
            run_repl()

        output = capsys.readouterr().out
        assert output.lower().count("unknown command") == 3

    def test_repl_shows_what_was_rejected(self, capsys):
        """The rejection message includes the input that was rejected."""
        user_inputs = ["cast lightning bolt", EOFError]
        with patch("builtins.input", side_effect=user_inputs):
            run_repl()

        output = capsys.readouterr().out
        assert "cast lightning bolt" in output

    def test_repl_exits_on_keyboard_interrupt(self):
        """The REPL exits cleanly on Ctrl-C."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            run_repl()  # should not raise

    def test_repl_prints_goodbye_on_exit(self, capsys):
        """The REPL prints a goodbye message when exiting."""
        with patch("builtins.input", side_effect=EOFError):
            run_repl()

        output = capsys.readouterr().out
        assert "goodbye" in output.lower()


class TestReplQuitExit:
    """The REPL exits cleanly when the user types 'quit' or 'exit'."""

    def test_repl_exits_on_quit_command(self, capsys):
        """Typing 'quit' exits the REPL without error."""
        with patch("builtins.input", side_effect=["quit"]):
            run_repl()

    def test_repl_exits_on_exit_command(self, capsys):
        """Typing 'exit' exits the REPL without error."""
        with patch("builtins.input", side_effect=["exit"]):
            run_repl()

    def test_repl_prints_goodbye_on_quit(self, capsys):
        """The REPL prints 'Goodbye.' when the user quits."""
        with patch("builtins.input", side_effect=["quit"]):
            run_repl()

        output = capsys.readouterr().out
        assert "goodbye" in output.lower()

    def test_repl_prints_goodbye_on_exit(self, capsys):
        """The REPL prints 'Goodbye.' when the user types exit."""
        with patch("builtins.input", side_effect=["exit"]):
            run_repl()

        output = capsys.readouterr().out
        assert "goodbye" in output.lower()

    def test_quit_does_not_print_unknown_command(self, capsys):
        """Typing 'quit' should not trigger the unknown command message."""
        with patch("builtins.input", side_effect=["quit"]):
            run_repl()

        output = capsys.readouterr().out
        assert "unknown command" not in output.lower()


class TestReplDecklistCommands:
    """The REPL dispatches decklist commands and prints handler output."""

    def test_repl_decklist_create_prints_confirmation(self, capsys):
        """'decklist create TestDeck' prints a creation confirmation."""
        with patch("builtins.input", side_effect=["decklist create TestDeck", "quit"]):
            run_repl()

        output = capsys.readouterr().out
        assert "created" in output.lower()
        assert "TestDeck" in output

    def test_repl_decklist_show_displays_summary(self, capsys):
        """'decklist show' prints the decklist summary."""
        with patch(
            "builtins.input",
            side_effect=["decklist create TestDeck", "decklist show", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "TestDeck" in output
        assert "Commander" in output


class TestReplCategoryCommands:
    """The REPL dispatches category commands and prints handler output."""

    def test_repl_category_create_prints_confirmation(self, capsys):
        """'category create Ramp 10' prints a creation confirmation."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Ramp" in output

    def test_repl_category_create_without_decklist_shows_error(self, capsys):
        """'category create' without a decklist shows an error."""
        with patch(
            "builtins.input",
            side_effect=["category create Ramp 10", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "no active decklist" in output.lower()

    def test_repl_category_list_displays_categories(self, capsys):
        """'category list' prints all categories."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "category list",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Commander" in output
        assert "Ramp" in output


class TestReplHelp:
    """The REPL displays help when the user types 'help'."""

    def test_repl_help_shows_commands(self, capsys):
        """'help' prints available commands."""
        with patch("builtins.input", side_effect=["help", "quit"]):
            run_repl()

        output = capsys.readouterr().out
        assert "decklist create" in output
        assert "category create" in output
        assert "help" in output


class TestReplCardAddCommands:
    """The REPL dispatches card add commands and prints handler output."""

    def test_repl_card_add_prints_confirmation(self, capsys):
        """'card add Ramp Sol Ring' prints a confirmation with card and category."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "card add Ramp Sol Ring",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Sol Ring" in output
        assert "Ramp" in output

    def test_repl_card_add_basic_land(self, capsys):
        """'card add Basic Lands Forest' prints a confirmation for Basic Lands."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "card add Basic Lands Forest",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Forest" in output
        assert "Basic Lands" in output

    def test_repl_card_add_without_decklist_shows_error(self, capsys):
        """'card add' without an active decklist prints an error."""
        with patch(
            "builtins.input",
            side_effect=["card add Ramp Sol Ring", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "no active decklist" in output.lower()


class TestReplUncategorizedWarning:
    """REPL prefixes every response with a warning while Uncategorized has cards."""

    def test_warning_shown_after_import_with_uncategorized_cards(
        self, capsys, tmp_path
    ):
        """Every command response is prefixed with the warning after import."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        with patch(
            "builtins.input",
            side_effect=[f"decklist import {f}", "category list", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "card(s) in Uncategorized" in output
        assert "Assign them to categories" in output

    def test_warning_not_shown_without_uncategorized_category(self, capsys):
        """No warning appears when the decklist has no Uncategorized category."""
        with patch(
            "builtins.input",
            side_effect=["decklist create TestDeck", "category list", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "card(s) in Uncategorized" not in output
