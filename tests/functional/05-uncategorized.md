# Uncategorized Warning System

The REPL prepends a warning to every command response while the Uncategorized
category has at least one card. The warning disappears once Uncategorized is
empty.

## Warning appears on every response while Uncategorized has cards

```scrut
$ printf "decklist import $TESTDIR/deck.txt\ncategory list\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Categories:
  Commander: 1/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Uncategorized: 1 slots filled (uncapped)
deckslots> Goodbye.
```

## No warning when decklist has no Uncategorized category

```scrut
$ printf 'decklist create TestDeck\ncategory list\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## Warning disappears after last card moved out of Uncategorized

Import creates 1 uncategorized card (Sol Ring). After category create (warning
still active), card move empties Uncategorized — subsequent category list has
no warning.

```scrut
$ printf "decklist import $TESTDIR/deck.txt\ncategory create Ramp 10\ncard move Sol Ring Ramp\ncategory list\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Created category 'Ramp' with 10 slots.
deckslots> Moved 'Sol Ring' from 'Uncategorized' to 'Ramp'.
deckslots> Categories:
  Commander: 1/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Uncategorized: 0 slots filled (uncapped)
  Ramp: 1/10 slots filled
deckslots> Goodbye.
```

## Warning disappears after last card deleted from Uncategorized

```scrut
$ printf "decklist import $TESTDIR/deck.txt\ncard delete Sol Ring\ncategory list\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.
deckslots> Deleted 'Sol Ring' from the decklist.
deckslots> Categories:
  Commander: 1/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Uncategorized: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## card remove activates warning on subsequent commands

card remove sends Sol Ring to Uncategorized, so the warning appears on the
card remove response and continues on subsequent commands.

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Sol Ring\ncard remove Sol Ring\ncategory list\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Removed 'Sol Ring' from 'Ramp'. Card is now in Uncategorized.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Ramp: 0/10 slots filled
  Uncategorized: 1 slots filled (uncapped)
deckslots> Goodbye.
```
