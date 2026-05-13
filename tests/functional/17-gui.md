# GUI subcommand

## `deckslots gui --help` lists the gui subcommand

```scrut
$ uv run deckslots gui --help
Usage: deckslots gui [OPTIONS]

  Launch the deckslots GUI.

Options:
  --help  Show this message and exit.
```

## `deckslots --help` mentions the gui subcommand

```scrut
$ uv run deckslots --help | grep -E "gui|Commands:"
Commands:
  gui  Launch the deckslots GUI.
```
