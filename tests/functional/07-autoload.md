# Auto-Load and Recovery Mode

On startup the REPL checks for a save file at
`$XDG_STATE_HOME/deckslots/decklist.bak`. If valid, it resumes silently. If
corrupt, it shows a recovery prompt.

Each test uses a distinct subdirectory of $TMPDIR for full isolation.
Two-block pattern: first block sets up state (no expected output), second block
runs the CLI and checks output.

---

## No Resumed message when no save file exists

```scrut
$ printf 'quit\n' | XDG_STATE_HOME="$TMPDIR/clean" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

## Resumed message appears before Welcome when save file is present

```scrut
$ mkdir -p "$TMPDIR/resume/deckslots" && printf '# My Deck\n\nCommander\n' > "$TMPDIR/resume/deckslots/decklist.bak"
```

```scrut
$ printf 'quit\n' | XDG_STATE_HOME="$TMPDIR/resume" uv run deckslots
Resumed 'My Deck'.
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

## Resumed message appears before Welcome (ordering check)

```scrut
$ mkdir -p "$TMPDIR/order/deckslots" && printf '# My Deck\n\nCommander\n' > "$TMPDIR/order/deckslots/decklist.bak"
```

```scrut
$ printf 'quit\n' | XDG_STATE_HOME="$TMPDIR/order" uv run deckslots
Resumed 'My Deck'.
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

---

## Corrupt save: warning and recovery options are shown

```scrut
$ mkdir -p "$TMPDIR/corrupt/deckslots" && printf 'not a valid save file\n' > "$TMPDIR/corrupt/deckslots/decklist.bak"
```

```scrut
$ printf 'exit\n' | XDG_STATE_HOME="$TMPDIR/corrupt" uv run deckslots
Warning: could not load save file: Save file missing '# <name>' header line..
Options:
  discard — delete the save file and start fresh
  exit    — quit so you can inspect the file manually
deckslots(recovery)> Goodbye.
```

## Corrupt save: 'discard' deletes the save file and continues to REPL

```scrut
$ mkdir -p "$TMPDIR/discard/deckslots" && printf 'not a valid save file\n' > "$TMPDIR/discard/deckslots/decklist.bak"
```

```scrut
$ printf 'discard\nquit\n' | XDG_STATE_HOME="$TMPDIR/discard" uv run deckslots
Warning: could not load save file: Save file missing '# <name>' header line..
Options:
  discard — delete the save file and start fresh
  exit    — quit so you can inspect the file manually
deckslots(recovery)> Save file deleted. Starting fresh.
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```

## Corrupt save: file is deleted after 'discard'

```scrut
$ mkdir -p "$TMPDIR/gone/deckslots" && printf 'not a valid save file\n' > "$TMPDIR/gone/deckslots/decklist.bak"
```

```scrut
$ printf 'discard\nquit\n' | XDG_STATE_HOME="$TMPDIR/gone" uv run deckslots > /dev/null
```

```scrut
$ test ! -f "$TMPDIR/gone/deckslots/decklist.bak" && echo "file deleted"
file deleted
```

## Corrupt save: 'exit' quits the program

```scrut
$ mkdir -p "$TMPDIR/exit/deckslots" && printf 'not a valid save file\n' > "$TMPDIR/exit/deckslots/decklist.bak"
```

```scrut
$ printf 'exit\n' | XDG_STATE_HOME="$TMPDIR/exit" uv run deckslots
Warning: could not load save file: Save file missing '# <name>' header line..
Options:
  discard — delete the save file and start fresh
  exit    — quit so you can inspect the file manually
deckslots(recovery)> Goodbye.
```

## Corrupt save: EOF quits the program

```scrut
$ mkdir -p "$TMPDIR/eof/deckslots" && printf 'not a valid save file\n' > "$TMPDIR/eof/deckslots/decklist.bak"
```

```scrut
$ printf '' | XDG_STATE_HOME="$TMPDIR/eof" uv run deckslots
Warning: could not load save file: Save file missing '# <name>' header line..
Options:
  discard — delete the save file and start fresh
  exit    — quit so you can inspect the file manually
deckslots(recovery)> Goodbye.
```

## Corrupt save: unrecognised input repeats the recovery prompt

The recovery prompt (`deckslots(recovery)> `) is printed without a trailing
newline. When the first input is unrecognised, the loop prints another prompt
immediately after — both appear on the same line.

```scrut
$ mkdir -p "$TMPDIR/repeat/deckslots" && printf 'not a valid save file\n' > "$TMPDIR/repeat/deckslots/decklist.bak"
```

```scrut
$ printf 'oops\nexit\n' | XDG_STATE_HOME="$TMPDIR/repeat" uv run deckslots
Warning: could not load save file: Save file missing '# <name>' header line..
Options:
  discard — delete the save file and start fresh
  exit    — quit so you can inspect the file manually
deckslots(recovery)> deckslots(recovery)> Goodbye.
```
