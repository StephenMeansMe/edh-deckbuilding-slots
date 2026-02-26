from unittest.mock import patch

from deckslots.repl import run_repl


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
