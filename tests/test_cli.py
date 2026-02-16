from deckslots.cli import parse_command


class TestParseCommand:
    """parse_command parses user input and checks it against known commands."""

    def test_unrecognized_input_is_unknown_command(self):
        """Input that doesn't match any known command is identified as unknown."""
        result = parse_command("hello")
        assert result.name == "hello"
        assert not result.known

    def test_empty_input_does_not_raise(self):
        """Empty input should not raise an IndexError."""
        result = parse_command("")
        assert result.name == ""
        assert not result.known

    def test_quit_is_recognized_as_known_command(self):
        """The 'quit' command is recognized as a known command."""
        result = parse_command("quit")
        assert result.known is True
