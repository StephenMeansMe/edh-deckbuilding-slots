from dataclasses import dataclass, field

import click

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


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """CLI entrypoint for deckslots.

    Running ``deckslots`` with no subcommand launches the interactive REPL,
    preserving backward compatibility. Use ``deckslots gui`` to launch the
    desktop application (requires the optional ``[gui]`` extra).
    """
    if ctx.invoked_subcommand is None:
        from deckslots.cli.repl import run_repl
        from deckslots.logging_config import setup_logging

        setup_logging()
        run_repl()


@main.command()
def gui() -> None:
    """Launch the deckslots GUI."""
    try:
        from deckslots.gui.app import run_app
    except ImportError as exc:
        click.echo(
            "GUI dependencies not installed. "
            "Install with: pip install 'deckslots[gui]'"
        )
        click.echo(f"  ({exc})")
        raise SystemExit(1) from exc
    run_app()


if __name__ == "__main__":
    main()
