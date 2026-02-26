# Category Commands

## category create prints confirmation with name and slot count

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Goodbye.
```

## category create without active decklist shows error

```scrut
$ printf 'category create Ramp 10\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## category list shows all categories including user-created ones

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncategory list\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Ramp: 0/10 slots filled
deckslots> Goodbye.
```
