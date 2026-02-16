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
