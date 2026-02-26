# Decklist Save and Load

Each test case uses a distinct subdirectory of $TMPDIR to prevent the save
file from one test bleeding into the next.

## decklist save persists the active decklist

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ndecklist save\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/t1" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Saved 'TestDeck'.
deckslots> Goodbye.
```

## decklist load restores a previously saved decklist

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ndecklist save\ndecklist load\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/t2" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Saved 'TestDeck'.
deckslots> Loaded 'TestDeck'.
deckslots> Decklist: TestDeck
Total slots: 11 (0 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Ramp: 0/10 slots filled
deckslots> Goodbye.
```

## decklist save without active decklist shows error

```scrut
$ printf 'decklist save\nquit\n' | XDG_STATE_HOME="$TMPDIR/t3" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## decklist load without a save file shows error

```scrut
$ printf 'decklist load\nquit\n' | XDG_STATE_HOME="$TMPDIR/t4" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No saved decklist found.
deckslots> Goodbye.
```
