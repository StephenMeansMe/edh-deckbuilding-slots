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
        # Two object_verb commands dispatched (import + category list) →
        # warning must appear twice to confirm it's truly persistent.
        assert output.count("card(s) in Uncategorized") == 2
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

    def test_warning_disappears_after_last_uncategorized_card_moved(
        self, capsys, tmp_path
    ):
        """Warning disappears once the last card is moved out of Uncategorized."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        with patch(
            "builtins.input",
            side_effect=[
                f"decklist import {f}",
                "category create Ramp 10",
                "card move Sol Ring Ramp",
                "category list",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        # Warning appears after import (Sol Ring in Uncategorized) and after
        # category create (Sol Ring still there), but NOT after card move
        # (Uncategorized now empty) or after category list (still empty).
        assert output.count("card(s) in Uncategorized") == 2

    def test_warning_disappears_after_last_uncategorized_card_deleted(
        self, capsys, tmp_path
    ):
        """Warning disappears once the last card is deleted from Uncategorized."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        with patch(
            "builtins.input",
            side_effect=[
                f"decklist import {f}",
                "card delete Sol Ring",
                "category list",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        # Warning appears after import (Sol Ring in Uncategorized), but NOT
        # after card delete (Uncategorized now empty) or category list.
        assert output.count("card(s) in Uncategorized") == 1

    def test_warning_shown_after_card_remove_sends_card_to_uncategorized(
        self, capsys
    ):
        """Warning appears on subsequent commands after 'card remove' populates Uncategorized."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "card add Ramp Sol Ring",
                "card remove Sol Ring",
                "category list",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        # Warning on card remove result (Sol Ring now in Uncategorized) and
        # on category list result (Sol Ring still there) — two appearances.
        assert output.count("card(s) in Uncategorized") == 2


class TestReplCardMoveCommands:
    """The REPL dispatches card move commands and prints handler output."""

    def test_card_move_success(self, capsys, tmp_path):
        """'card move <card> <category>' moves card and prints confirmation."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        with patch(
            "builtins.input",
            side_effect=[
                f"decklist import {f}",
                "category create Ramp 10",
                "card move Sol Ring Ramp",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Moved" in output
        assert "Sol Ring" in output
        assert "Ramp" in output

    def test_card_move_reports_source_and_target_category(self, capsys, tmp_path):
        """Success message names both the source and destination categories."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        with patch(
            "builtins.input",
            side_effect=[
                f"decklist import {f}",
                "category create Ramp 10",
                "card move Sol Ring Ramp",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Uncategorized" in output
        assert "Ramp" in output

    def test_card_move_error_card_not_found(self, capsys):
        """'card move' with an unknown card name prints an error."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "card move Nonexistent Ramp",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "not found" in output.lower()

    def test_card_move_error_category_not_found(self, capsys, tmp_path):
        """'card move' with an unknown category name prints an error."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        with patch(
            "builtins.input",
            side_effect=[
                f"decklist import {f}",
                "card move Sol Ring NoSuchCategory",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "not found" in output.lower()

    def test_card_move_without_decklist_shows_error(self, capsys):
        """'card move' without an active decklist prints an error."""
        with patch(
            "builtins.input",
            side_effect=["card move Sol Ring Ramp", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "no active decklist" in output.lower()


class TestReplCardRemoveCommands:
    """The REPL dispatches card remove commands and prints handler output."""

    def test_card_remove_moves_card_to_uncategorized(self, capsys):
        """'card remove <card>' moves card to Uncategorized and prints confirmation."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "card add Ramp Sol Ring",
                "card remove Sol Ring",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Uncategorized" in output
        assert "Sol Ring" in output

    def test_card_remove_activates_warning_on_subsequent_command(self, capsys):
        """After 'card remove', the next command output is prefixed with the warning."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "card add Ramp Sol Ring",
                "card remove Sol Ring",
                "category list",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "card(s) in Uncategorized" in output

    def test_card_remove_error_card_not_found(self, capsys):
        """'card remove' with an unknown card name prints an error."""
        with patch(
            "builtins.input",
            side_effect=["decklist create TestDeck", "card remove Nonexistent", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "not found" in output.lower()

    def test_card_remove_without_decklist_shows_error(self, capsys):
        """'card remove' without an active decklist prints an error."""
        with patch(
            "builtins.input",
            side_effect=["card remove Sol Ring", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "no active decklist" in output.lower()


class TestReplCardDeleteCommands:
    """The REPL dispatches card delete commands and prints handler output."""

    def test_card_delete_removes_card_and_prints_confirmation(self, capsys):
        """'card delete <card>' deletes the card and prints confirmation."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "card add Ramp Sol Ring",
                "card delete Sol Ring",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Deleted" in output
        assert "Sol Ring" in output

    def test_card_delete_does_not_trigger_uncategorized_warning(self, capsys):
        """'card delete' from a named category does not trigger the Uncategorized warning."""
        with patch(
            "builtins.input",
            side_effect=[
                "decklist create TestDeck",
                "category create Ramp 10",
                "card add Ramp Sol Ring",
                "card delete Sol Ring",
                "category list",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "card(s) in Uncategorized" not in output

    def test_card_delete_from_uncategorized(self, capsys, tmp_path):
        """'card delete' can permanently remove a card from Uncategorized."""
        f = tmp_path / "MyDeck.txt"
        f.write_text("Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n")
        with patch(
            "builtins.input",
            side_effect=[
                f"decklist import {f}",
                "card delete Sol Ring",
                "quit",
            ],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "Deleted" in output
        assert "Sol Ring" in output

    def test_card_delete_without_decklist_shows_error(self, capsys):
        """'card delete' without an active decklist prints an error."""
        with patch(
            "builtins.input",
            side_effect=["card delete Sol Ring", "quit"],
        ):
            run_repl()

        output = capsys.readouterr().out
        assert "no active decklist" in output.lower()


def _write_save(tmp_path, monkeypatch, content):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    save = tmp_path / "deckslots" / "decklist.bak"
    save.parent.mkdir(parents=True)
    save.write_text(content)
    return save


class TestReplAutoLoad:
    def test_resumes_deck_on_startup_when_save_file_exists(
        self, monkeypatch, tmp_path, capsys
    ):
        """run_repl prints 'Resumed ...' before the welcome when a save file exists."""
        _write_save(tmp_path, monkeypatch, "# My Deck\n\nCommander\n")
        with patch("builtins.input", side_effect=EOFError):
            run_repl()
        output = capsys.readouterr().out
        assert "Resumed 'My Deck'." in output

    def test_resumed_message_appears_before_welcome(
        self, monkeypatch, tmp_path, capsys
    ):
        """The 'Resumed' line is printed before the welcome line."""
        _write_save(tmp_path, monkeypatch, "# My Deck\n\nCommander\n")
        with patch("builtins.input", side_effect=EOFError):
            run_repl()
        output = capsys.readouterr().out
        assert output.index("Resumed") < output.index("Welcome")

    def test_no_resume_message_when_save_file_absent(
        self, monkeypatch, tmp_path, capsys
    ):
        """run_repl starts silently when no save file exists."""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        with patch("builtins.input", side_effect=EOFError):
            run_repl()
        output = capsys.readouterr().out
        assert "Resumed" not in output

    def test_corrupt_save_shows_warning_and_recovery_prompt(
        self, monkeypatch, tmp_path, capsys
    ):
        """A corrupt save file shows a warning and recovery prompt."""
        _write_save(tmp_path, monkeypatch, "not a valid save file\n")
        with patch("builtins.input", side_effect=["exit"]):
            run_repl()
        output = capsys.readouterr().out
        assert "Warning" in output
        assert "discard" in output.lower()
        assert "exit" in output.lower()

    def test_recovery_discard_deletes_file_and_continues(
        self, monkeypatch, tmp_path, capsys
    ):
        """Typing 'discard' at the recovery prompt deletes the file and continues."""
        save = _write_save(tmp_path, monkeypatch, "not a valid save file\n")
        with patch("builtins.input", side_effect=["discard", "quit"]):
            run_repl()
        assert not save.exists()
        output = capsys.readouterr().out
        assert "Starting fresh" in output

    def test_recovery_exit_quits_program(self, monkeypatch, tmp_path, capsys):
        """Typing 'exit' at the recovery prompt exits the program."""
        _write_save(tmp_path, monkeypatch, "not a valid save file\n")
        with patch("builtins.input", side_effect=["exit"]):
            run_repl()
        output = capsys.readouterr().out
        assert "Goodbye" in output

    def test_recovery_eof_exits_program(self, monkeypatch, tmp_path, capsys):
        """EOF at the recovery prompt exits the program."""
        _write_save(tmp_path, monkeypatch, "not a valid save file\n")
        with patch("builtins.input", side_effect=EOFError):
            run_repl()
        output = capsys.readouterr().out
        assert "Goodbye" in output

    def test_recovery_unknown_input_repeats_prompt(self, monkeypatch, tmp_path, capsys):
        """Unrecognised input at the recovery prompt repeats without crashing."""
        _write_save(tmp_path, monkeypatch, "not a valid save file\n")
        with patch("builtins.input", side_effect=["oops", "exit"]):
            run_repl()
        output = capsys.readouterr().out
        # Recovery prompt appears at least twice (once for 'oops', once for 'exit')
        assert output.count("deckslots(recovery)>") >= 2
