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

    def test_help_parses_as_builtin(self):
        """The 'help' command is parsed as a builtin."""
        result = parse_command("help")
        assert result.kind == "builtin"
        assert result.builtin == "help"

    def test_decklist_create_parses_as_object_verb(self):
        """'decklist create MyDeck' parses as an object-verb command."""
        result = parse_command("decklist create MyDeck")
        assert result.kind == "object_verb"
        assert result.obj == "decklist"
        assert result.verb == "create"
        assert result.args == ["MyDeck"]

    def test_category_create_parses_with_two_args(self):
        """'category create Ramp 10' captures both args."""
        result = parse_command("category create Ramp 10")
        assert result.kind == "object_verb"
        assert result.obj == "category"
        assert result.verb == "create"
        assert result.args == ["Ramp", "10"]

    def test_object_verb_case_insensitive(self):
        """Object and verb are lowercased; args preserve original casing."""
        result = parse_command("Decklist Create MyDeck")
        assert result.obj == "decklist"
        assert result.verb == "create"
        assert result.args == ["MyDeck"]

    def test_object_alone_is_unknown(self):
        """A known object without a verb is parsed as unknown."""
        result = parse_command("decklist")
        assert result.kind == "unknown"
