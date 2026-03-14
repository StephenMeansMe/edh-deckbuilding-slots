import click
from dataclasses import dataclass, field

BUILTINS: set[str] = {"quit", "exit", "help"}
KNOWN_OBJECTS: set[str] = {"decklist", "category", "card", "template"}


@dataclass
class ParsedCommand:
    kind: str
    raw: str
    builtin: str | None = None
    obj: str | None = None
    verb: str | None = None
    args: list[str] = field(default_factory=list)


def parse_command(line: str) -> ParsedCommand:
    """Parse user input into a structured command."""
    stripped = line.strip()
    if not stripped:
        return ParsedCommand(kind="empty", raw=stripped)
    parts = stripped.split()
    word = parts[0].lower()
    if word in BUILTINS:
        return ParsedCommand(kind="builtin", raw=stripped, builtin=word)
    if word in KNOWN_OBJECTS and len(parts) >= 2:
        verb = parts[1].lower()
        args = parts[2:]
        return ParsedCommand(
            kind="object_verb", raw=stripped, obj=word, verb=verb, args=args
        )
    return ParsedCommand(kind="unknown", raw=stripped)


@click.command()
def main() -> None:
    """CLI entrypoint for deckslots."""
    from deckslots.logging_config import setup_logging
    from deckslots.repl import run_repl

    setup_logging()
    run_repl()


if __name__ == "__main__":
    main()
