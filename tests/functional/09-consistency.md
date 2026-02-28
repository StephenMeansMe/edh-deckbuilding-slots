# Deck Consistency Checks (US-006)

## Setup: import file with Sol Ring listed twice (to exercise singleton move check)

```scrut
$ printf 'Commander\n1 Atraxa\n\nMaindeck\n1 Sol Ring\n1 Sol Ring\n' > "$TMPDIR/double.txt"
```

---

## card move to same category is a no-op (AC 1)

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Sol Ring\ncard move Sol Ring Ramp\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/noop" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> 'Sol Ring' is already in 'Ramp'. Nothing to do.
deckslots> Goodbye.
```

---

## card add rejects a basic land added to a non-Basic-Lands category (AC 5)

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Ramp Forest\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/basicadd" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Error: Basic lands can only be added to the 'Basic Lands' category.
deckslots> Goodbye.
```

---

## card move rejects moving a basic land to a non-Basic-Lands category (AC 6)

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncard add Basic Lands Forest\ncard move Forest Ramp\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/basicmove" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Forest' to 'Basic Lands'.
deckslots> Error: Basic lands can only be added to the 'Basic Lands' category.
deckslots> Goodbye.
```

---

## card move enforces singleton rule (AC 2)

Import a deck where Sol Ring appears twice in Maindeck.  Both land in
Uncategorized.  Move the first copy to Ramp, then attempt to move the second
copy to Draw — which must be rejected because Sol Ring is already in the capped
Ramp category.

```scrut
$ printf "decklist import $TMPDIR/double.txt\ncategory create Ramp 10\ncategory create Draw 10\ncard move Sol Ring Ramp\ncard move Sol Ring Draw\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR/singleton" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 2 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'double': 1 commander, 0 basic lands, 2 uncategorized cards.
deckslots> Warning: 2 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Created category 'Ramp' with 10 slots.
deckslots> Warning: 2 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Created category 'Draw' with 10 slots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Moved 'Sol Ring' from 'Uncategorized' to 'Ramp'.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Error: 'Sol Ring' is already in the deck (in 'Ramp').
deckslots> Goodbye.
```
