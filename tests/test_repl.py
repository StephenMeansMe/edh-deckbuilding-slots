from unittest.mock import patch

from deckslots.repl import run_repl


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
