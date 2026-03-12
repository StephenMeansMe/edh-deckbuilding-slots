# Companion Slot

## enable-companion shows Companion category in decklist show

```scrut
$ printf 'decklist create LurrusDeck\ndecklist enable-companion\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'LurrusDeck'.
deckslots> Companion slot enabled. Add a companion with 'card add Companion <card name>'.
deckslots> Warning: Companion slot is empty. Add a companion with 'card add Companion <card name>'.
Decklist: LurrusDeck
Total slots: 2 (0 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Companion: 0/1 slots filled
deckslots> Goodbye.
```

## enable-companion without active decklist shows error

```scrut
$ printf 'decklist enable-companion\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## disable-companion moves card to Uncategorized

```scrut
$ printf 'decklist create LurrusDeck\ndecklist enable-companion\ncard add Companion Lurrus of the Dream-Den\ndecklist disable-companion\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'LurrusDeck'.
deckslots> Companion slot enabled. Add a companion with 'card add Companion <card name>'.
deckslots> Added 'Lurrus of the Dream-Den' to 'Companion'.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Companion mode disabled. All companion cards moved to Uncategorized.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Decklist: LurrusDeck
Total slots: 1 (1 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Uncategorized: 1 slots filled (uncapped)
deckslots> Goodbye.
```

## save and load round-trip preserves companion card

```scrut
$ printf 'decklist create LurrusDeck\ndecklist enable-companion\ncard add Companion Lurrus of the Dream-Den\ndecklist save\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'LurrusDeck'.
deckslots> Companion slot enabled. Add a companion with 'card add Companion <card name>'.
deckslots> Added 'Lurrus of the Dream-Den' to 'Companion'.
deckslots> Saved 'LurrusDeck'.
deckslots> Goodbye.
```

```scrut
$ printf 'decklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
Resumed 'LurrusDeck'.
deckslots> Welcome to deckslots.
deckslots> Decklist: LurrusDeck
Total slots: 2 (1 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Companion: 1/1 slots filled
deckslots> Goodbye.
```

## export writes Companion section; card excluded from Maindeck

```scrut
$ printf 'decklist create LurrusDeck\ndecklist enable-companion\ncard add Companion Lurrus of the Dream-Den\ndecklist export %s/export.txt\nquit\n' "$TMPDIR" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots \
>   | grep -v "^deckslots> Exported"
deckslots> Welcome to deckslots.
deckslots> Created decklist 'LurrusDeck'.
deckslots> Companion slot enabled. Add a companion with 'card add Companion <card name>'.
deckslots> Added 'Lurrus of the Dream-Den' to 'Companion'.
deckslots> Goodbye.
```

## export file contains Companion section before Maindeck

```scrut
$ printf 'decklist create LurrusDeck\ndecklist enable-companion\ncard add Companion Lurrus of the Dream-Den\ndecklist export %s/export2.txt\nquit\n' "$TMPDIR" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots > /dev/null && cat "$TMPDIR/export2.txt"
Commander

Companion
1 Lurrus of the Dream-Den

Maindeck
```

## export-import round-trip restores companion mode

```scrut
$ printf 'decklist create LurrusDeck\ndecklist enable-companion\ncard add Companion Lurrus of the Dream-Den\ndecklist export %s/round-trip.txt\nquit\n' "$TMPDIR" \
>   | XDG_STATE_HOME="$TMPDIR/state1" uv run deckslots > /dev/null && printf 'decklist import %s/round-trip.txt\ndecklist show\nquit\n' "$TMPDIR" \
>   | XDG_STATE_HOME="$TMPDIR/state2" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Imported 'round-trip': 0 commander, 0 basic lands, 0 uncategorized cards.
Warning: no commander found in file.
deckslots> Decklist: round-trip
Total slots: 2 (1 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Companion: 1/1 slots filled
  Uncategorized: 0 slots filled (uncapped)
deckslots> Goodbye.
```
