from dataclasses import dataclass, field

BUILTINS: set[str] = {"quit", "exit"}


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
    return ParsedCommand(kind="unknown", raw=stripped)


def main():
    """CLI entrypoint for deckslots."""
    from deckslots.repl import run_repl

    run_repl()


if __name__ == "__main__":
    main()
