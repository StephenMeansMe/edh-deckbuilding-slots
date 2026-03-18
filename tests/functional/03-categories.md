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

## category resize changes slot count

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncategory resize Ramp 8\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Resized 'Ramp' to 8 slots.
deckslots> Goodbye.
```

## category resize without active decklist shows error

```scrut
$ printf 'category resize Ramp 8\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## category resize on fixed category shows error

```scrut
$ printf 'decklist create TestDeck\ncategory resize Commander 2\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Cannot resize fixed category 'Commander'.
deckslots> Goodbye.
```

## category delete removes category and confirms

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncategory delete Ramp\ncategory list\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Deleted category 'Ramp'.
deckslots> Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## category delete with cards moves them to Uncategorized

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Sol Ring\ncategory delete Ramp\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Deleted category 'Ramp'. 1 card(s) moved to Uncategorized.
deckslots> Warning: Uncategorized is non-empty. Assign cards to categories.
deckslots> Goodbye.
```

## category delete without active decklist shows error

```scrut
$ printf 'category delete Ramp\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## category delete on fixed category shows error

```scrut
$ printf 'decklist create TestDeck\ncategory delete Commander\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Cannot delete fixed category 'Commander'.
deckslots> Goodbye.
```

## category show displays category details

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncategory show Ramp\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Ramp: 0/10 slots filled
deckslots> Goodbye.
```

## category show without active decklist shows error

```scrut
$ printf 'category show Ramp\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## category show for nonexistent category shows error

```scrut
$ printf 'decklist create TestDeck\ncategory show Nonexistent\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Category 'Nonexistent' not found.
deckslots> Goodbye.
```
