# Partner Commanders

## decklist enable-partners allows two commanders

```scrut
$ printf 'decklist create PartnerDeck\ndecklist enable-partners\ncard add Commander Malcolm, Keen-Eyed Navigator\ncard add Commander Tana, the Bloodsower\ndecklist show\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'PartnerDeck'.
deckslots> Partners mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Malcolm, Keen-Eyed Navigator' to 'Commander'.
deckslots> Added 'Tana, the Bloodsower' to 'Commander'.
deckslots> Decklist: PartnerDeck
Total slots: 2 (2 filled)
Categories:
  Commander: 2/2 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```

## decklist enable-partners without active decklist shows error

```scrut
$ printf 'decklist enable-partners\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## partners mode survives save and load round-trip

```scrut
$ printf 'decklist create PartnerDeck\ndecklist enable-partners\ncard add Commander Malcolm, Keen-Eyed Navigator\ncard add Commander Tana, the Bloodsower\ndecklist save\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'PartnerDeck'.
deckslots> Partners mode enabled. The Commander category now has 2 slots.
deckslots> Added 'Malcolm, Keen-Eyed Navigator' to 'Commander'.
deckslots> Added 'Tana, the Bloodsower' to 'Commander'.
deckslots> Saved 'PartnerDeck'.
deckslots> Goodbye.
```

```scrut
$ printf 'decklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR/state" uv run deckslots
Resumed 'PartnerDeck'.
deckslots> Welcome to deckslots.
deckslots> Warning: Commander has more cards than enabled modes allow. Run 'decklist enable-partners' or 'decklist enable-background', or use 'card move' to reassign the extra cards.
Decklist: PartnerDeck
Total slots: 2 (2 filled)
Categories:
  Commander: 2/2 slots filled
  Basic Lands: 0 slots filled (uncapped)
deckslots> Goodbye.
```
