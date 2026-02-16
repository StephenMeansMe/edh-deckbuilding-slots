from dataclasses import dataclass

KNOWN_COMMANDS: dict[str, object] = {}


@dataclass
class ParsedCommand:
    name: str
    known: bool


def parse_command(line: str) -> ParsedCommand:
    """Parse user input and check the command word against known commands."""
    name = line.split()[0]
    return ParsedCommand(name=name, known=name in KNOWN_COMMANDS)


def main():
    """CLI entrypoint for deckslots."""
    from deckslots.repl import run_repl

    run_repl()


if __name__ == "__main__":
    main()
