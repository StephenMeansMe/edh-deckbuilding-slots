# Rename Commands

## decklist rename prompts for and applies new name

```scrut
$ printf 'decklist create TestDeck\ndecklist rename\nMy Commander Deck\ndecklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> New name: Renamed decklist to 'My Commander Deck'.
deckslots> Decklist: My Commander Deck
Total slots: 1 (0 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## decklist rename without active decklist shows error

```scrut
$ printf 'decklist rename\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## category rename prompts for and applies new name

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncategory rename Ramp\nMana Rocks\ncategory list\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> New name: Renamed category 'Ramp' to 'Mana Rocks'.
deckslots> Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Mana Rocks: 0/10 slots filled
deckslots> Goodbye.
```

## category rename with multi-word category name

```scrut
$ printf 'decklist create TestDeck\ncategory create Mana Ramp 10\ncategory rename Mana Ramp\nAcceleration Package\ncategory list\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Mana Ramp' with 10 slots.
deckslots> New name: Renamed category 'Mana Ramp' to 'Acceleration Package'.
deckslots> Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Acceleration Package: 0/10 slots filled
deckslots> Goodbye.
```

## category rename fixed category shows error without prompting

```scrut
$ printf 'decklist create TestDeck\ncategory rename commander\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Cannot rename fixed category 'Commander'.
deckslots> Goodbye.
```

## category rename nonexistent category shows error without prompting

```scrut
$ printf 'decklist create TestDeck\ncategory rename nonexistent\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Category 'nonexistent' not found.
deckslots> Goodbye.
```

## category rename without args shows usage

```scrut
$ printf 'decklist create TestDeck\ncategory rename\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Usage: category rename <name>
deckslots> Goodbye.
```

## rename persists through save and load

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncategory rename Ramp\nMana Rocks\ndecklist save\ndecklist load\ncategory list\nquit\n' | XDG_STATE_HOME="$TMPDIR/rename-persist" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> New name: Renamed category 'Ramp' to 'Mana Rocks'.
deckslots> Saved 'TestDeck'.
deckslots> Loaded 'TestDeck'.
deckslots> Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Mana Rocks: 0/10 slots filled
deckslots> Goodbye.
```
