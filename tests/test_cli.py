from deckslots.cli import parse_command


class TestParseCommand:
    """parse_command parses user input and checks it against known commands."""

    def test_unrecognized_input_is_unknown_command(self):
        """Input that doesn't match any known command is identified as unknown."""
        result = parse_command("hello")
        assert result.name == "hello"
        assert not result.known
