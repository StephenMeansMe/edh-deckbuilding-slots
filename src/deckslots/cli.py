from dataclasses import dataclass

from deckslots.repl import run_repl

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
    run_repl()


if __name__ == "__main__":
    main()
