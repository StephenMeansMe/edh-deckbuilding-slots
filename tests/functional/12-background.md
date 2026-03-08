# Background Commanders

## decklist enable-background allows two commanders

```scrut
$ printf 'decklist create BgDeck\ndecklist enable-background\ncard add Commander Cloakwood Hermit\ncard add Commander Criminal Past\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'BgDeck'.
deckslots> Background mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Cloakwood Hermit' to 'Commander'.
deckslots> Added 'Criminal Past' to 'Commander'.
deckslots> Decklist: BgDeck
Total slots: 2 (2 filled)
Categories:
  Commander: 2/2 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## decklist enable-background without active decklist shows error

```scrut
$ printf 'decklist enable-background\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## decklist disable-partners moves all commanders to Uncategorized

```scrut
$ printf 'decklist create PartnerDeck\ndecklist enable-partners\ncard add Commander Malcolm, Keen-Eyed Navigator\ncard add Commander Tana, the Bloodsower\ndecklist disable-partners\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'PartnerDeck'.
deckslots> Partners mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Malcolm, Keen-Eyed Navigator' to 'Commander'.
deckslots> Added 'Tana, the Bloodsower' to 'Commander'.
deckslots> Warning: 2 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Partners mode disabled. All commanders moved to Uncategorized.
deckslots> Warning: 2 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Decklist: PartnerDeck
Total slots: 1 (2 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Uncategorized: 2 slots filled (uncapped)
deckslots> Goodbye.
```

## both modes enabled gives three Commander slots

```scrut
$ printf 'decklist create Hybrid\ndecklist enable-partners\ndecklist enable-background\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Hybrid'.
deckslots> Partners mode enabled. The Commander category now has 2 slots.
deckslots> Background mode enabled. The Commander category now has 3 slots.
deckslots> Decklist: Hybrid
Total slots: 3 (0 filled)
Categories:
  Commander: 0/3 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## overcrowded warning fires after loading a save with two commanders and no mode

```scrut
$ printf 'decklist create BgDeck\ndecklist enable-background\ncard add Commander Cloakwood Hermit\ncard add Commander Criminal Past\ndecklist save\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'BgDeck'.
deckslots> Background mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Cloakwood Hermit' to 'Commander'.
deckslots> Added 'Criminal Past' to 'Commander'.
deckslots> Saved 'BgDeck'.
deckslots> Goodbye.
```

```scrut
$ printf 'decklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
Resumed 'BgDeck'.
deckslots> Welcome to deckslots.
deckslots> Warning: Commander has more cards than enabled modes allow. Run 'decklist enable-partners' or 'decklist enable-background', or use 'card move' to reassign the extra cards.
Decklist: BgDeck
Total slots: 2 (2 filled)
Categories:
  Commander: 2/2 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```
