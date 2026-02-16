from deckslots.cli import parse_command


class TestParseCommand:
    """parse_command parses user input into a structured ParsedCommand."""

    def test_quit_parses_as_builtin(self):
        """'quit' is parsed as a builtin command."""
        result = parse_command("quit")
        assert result.kind == "builtin"
        assert result.builtin == "quit"

    def test_unrecognized_input_is_unknown_command(self):
        """Input that doesn't match any known command is identified as unknown."""
        result = parse_command("hello")
        assert result.kind == "unknown"
        assert result.raw == "hello"

    def test_empty_input_parses_as_empty(self):
        """Empty input is parsed as kind 'empty'."""
        result = parse_command("")
        assert result.kind == "empty"

    def test_exit_parses_as_builtin(self):
        """The 'exit' command is parsed as a builtin."""
        result = parse_command("exit")
        assert result.kind == "builtin"
        assert result.builtin == "exit"
