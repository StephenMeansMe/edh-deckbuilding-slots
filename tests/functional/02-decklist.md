# Decklist Commands

## decklist create prints confirmation with name

```scrut
$ printf 'decklist create TestDeck\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Goodbye.
```

## decklist show displays name and category summary

```scrut
$ printf 'decklist create TestDeck\ndecklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Decklist: TestDeck
Total slots: 1 (0 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## decklist create without name shows usage error

```scrut
$ printf 'decklist create\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Usage: decklist create <name>
deckslots> Goodbye.
```

## decklist show without active decklist shows error

```scrut
$ printf 'decklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```
