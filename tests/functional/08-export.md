# Decklist Export

Each test case uses a distinct subdirectory of $TMPDIR to prevent state from
one test bleeding into the next.

The export success message includes the filepath, which contains the
scrut-managed $TMPDIR value and cannot be matched literally. Tests that need
to verify the success message pipe REPL output through
`grep -v "^deckslots> Exported"` so that all other output lines are still
asserted exactly. The exact message format (including the filepath) is covered
by the pytest unit tests.

## decklist export writes file and prints REPL output

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 2\ncard add Ramp Sol Ring\ncard add Ramp Cultivate\ndecklist export '"$TMPDIR/t1/deck.txt"'\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/t1" uv run deckslots | grep -v "^deckslots> Exported"
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 2 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Added 'Cultivate' to 'Ramp'.
deckslots> Goodbye.
```

## exported file has Commander and Maindeck sections with correct cards

```scrut
$ cat "$TMPDIR/t1/deck.txt"
Commander

Maindeck
1 Cultivate
1 Sol Ring
```

## decklist export with a commander card writes commander in Commander section

```scrut
$ printf 'decklist create MyDeck\ncard add Commander Atraxa, Praetors'"'"' Voice\ndecklist export '"$TMPDIR/t2/deck.txt"'\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/t2" uv run deckslots | grep -v "^deckslots> Exported"
deckslots> Welcome to deckslots.
deckslots> Created decklist 'MyDeck'.
deckslots> Added 'Atraxa, Praetors' Voice' to 'Commander'.
deckslots> Goodbye.
```

## commander export file has correct Commander section

```scrut
$ cat "$TMPDIR/t2/deck.txt"
Commander
1 Atraxa, Praetors' Voice

Maindeck
```

## decklist export without active decklist shows error

```scrut
$ printf 'decklist export '"$TMPDIR/t3/deck.txt"'\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/t3" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## decklist export without filepath shows usage

```scrut
$ printf 'decklist create TestDeck\ndecklist export\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/t4" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Usage: decklist export <filepath>
deckslots> Goodbye.
```
