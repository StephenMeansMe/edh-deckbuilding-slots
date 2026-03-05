# Card Commands

## card add to a named category

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Sol Ring\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Goodbye.
```

## card add to Basic Lands (multi-word category name)

```scrut
$ printf 'decklist create TestDeck\ncard add Basic Lands Forest\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Added 'Forest' to 'Basic Lands'.
deckslots> Goodbye.
```

## card add without active decklist shows error

```scrut
$ printf 'card add Ramp Sol Ring\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

---

## card move reports source and destination categories

```scrut
$ printf "decklist import $TESTDIR/deck.txt\ncategory create Ramp 10\ncard move Sol Ring Ramp\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Created category 'Ramp' with 10 slots.
deckslots> Moved 'Sol Ring' from 'Uncategorized' to 'Ramp'.
deckslots> Goodbye.
```

## card move error: card not found

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard move Nonexistent Ramp\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Card 'Nonexistent' not found in the decklist.
deckslots> Goodbye.
```

## card move error: category not found

```scrut
$ printf "decklist import $TESTDIR/deck.txt\ncard move Sol Ring NoSuchCategory\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Category not found. Usage: card move <card-name> <to-category>
deckslots> Goodbye.
```

## card move without active decklist shows error

```scrut
$ printf 'card move Sol Ring Ramp\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

---

## card remove moves card to Uncategorized

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Sol Ring\ncard remove Sol Ring\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Removed 'Sol Ring' from 'Ramp'. Card is now in Uncategorized.
deckslots> Goodbye.
```

## card remove error: card not found

```scrut
$ printf 'decklist create TestDeck\ncard remove Nonexistent\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Card 'Nonexistent' not found in the decklist.
deckslots> Goodbye.
```

## card remove without active decklist shows error

```scrut
$ printf 'card remove Sol Ring\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

---

## card delete permanently removes a card from a named category

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Sol Ring\ncard delete Sol Ring\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Deleted 'Sol Ring' from the decklist.
deckslots> Goodbye.
```

## card delete from Uncategorized (after import)

```scrut
$ printf "decklist import $TESTDIR/deck.txt\ncard delete Sol Ring\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.
deckslots> Deleted 'Sol Ring' from the decklist.
deckslots> Goodbye.
```

## card delete does not trigger Uncategorized warning

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Sol Ring\ncard delete Sol Ring\ncategory list\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Deleted 'Sol Ring' from the decklist.
deckslots> Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Ramp: 0/10 slots filled
deckslots> Goodbye.
```

## card delete without active decklist shows error

```scrut
$ printf 'card delete Sol Ring\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```
