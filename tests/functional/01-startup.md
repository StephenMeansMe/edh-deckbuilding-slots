# REPL Startup, Quit/Exit, and Help

## EOF exits cleanly and prints Goodbye

```scrut
$ printf '' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

## quit exits cleanly and prints Goodbye

```scrut
$ printf 'quit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

## exit exits cleanly and prints Goodbye

```scrut
$ printf 'exit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

## quit does not print unknown-command error

```scrut
$ printf 'quit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

## Unknown command echoes the rejected input

```scrut
$ printf 'cast lightning bolt\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Unknown command: cast lightning bolt
deckslots> Goodbye.
```

## Multiple unknown commands are each rejected

```scrut
$ printf 'foo\nbar\nbaz\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Unknown command: foo
deckslots> Unknown command: bar
deckslots> Unknown command: baz
deckslots> Goodbye.
```

## help shows all available commands

```scrut
$ printf 'help\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Available commands:
  decklist create <name>        Create a new decklist
  decklist show                 Show the active decklist
  decklist import <file>        Import a decklist from a text file
  decklist export <file>        Export the active decklist to a text file
  decklist save                 Save the active decklist
  decklist load                 Load the last saved decklist
  decklist list                 List all saved decks
  decklist switch <name>        Switch the active deck to a saved one
  decklist delete <name>        Remove a saved deck (prompts to confirm)
  decklist rename               Rename the active decklist
  decklist apply-template <n>   Apply a template to the active decklist
  decklist enable-partners      Allow two commanders (partner mechanic)
  decklist enable-background    Allow a Background co-commander
  decklist disable-partners     Disable partners; move commanders out
  decklist disable-background   Disable background; move commanders out
  decklist enable-companion     Enable a companion (separate zone)
  decklist disable-companion    Disable companion; move to Uncategorized
  category create <n> <s>       Add a category with <s> slots
  category list                 List all categories
  category rename <name>        Rename a user-created category
  category resize <name> <s>    Resize a user-created category
  category delete <name>        Delete a user-created category
  category show <name>          Show details of a category
  card add <cat> <name>         Add a card to a category
  card move <name> <cat>        Move a card to a different category
  card remove <name>            Move a card to Uncategorized
  card delete <name>            Permanently remove a card
  template list                 List all available templates
  template save <name>          Save current categories as a template
  template export <n> <file>    Export a named template to a file
  template import <file>        Import a template from a file
  help                          Show this help message
  quit / exit                   Exit the program
deckslots> Goodbye.
```
