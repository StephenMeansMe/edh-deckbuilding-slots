"""CLI subpackage for deckslots: parser, REPL, command handlers, status line.

Re-exports the public surface so existing imports like
``from deckslots.cli import ParsedCommand, parse_command, main`` continue to work
and the ``pyproject.toml`` entry point ``deckslots.cli:main`` keeps resolving.
"""

from deckslots.cli.parser import ParsedCommand, main, parse_command

__all__ = ["ParsedCommand", "main", "parse_command"]
