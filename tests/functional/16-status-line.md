# Status Line

The REPL displays a compact status line after every command showing the active
decklist name, capped-slot fill progress, and any warning indicators.

## Status line appears after decklist create

```scrut
$ printf 'decklist create TestDeck\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
TestDeck (0/1)
deckslots> Goodbye.
```

## Status line updates slot count after category create

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
TestDeck (0/1)
deckslots> Created category 'Ramp' with 10 slots.
TestDeck (0/11)
deckslots> Goodbye.
```

## Status line shows compact Uncategorized warning alongside verbose warning

```scrut
$ printf "decklist import $TESTDIR/deck.txt\nquit\n" \
>   | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Imported 'deck': 1 commander, 0 basic lands, 1 uncategorized cards.
deck (1/1) | Uncategorized: 1
deckslots> Goodbye.
```

## Status line shows Validation: OFF when validation disabled

```scrut
$ mkdir -p "$TMPDIR/conf_off/deckslots" \
>   && printf '{"validation_enabled": false}' > "$TMPDIR/conf_off/deckslots/config.json" \
>   && printf 'decklist create TestDeck\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" XDG_CONFIG_HOME="$TMPDIR/conf_off" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
TestDeck (0/1) | Validation: OFF
deckslots> Goodbye.
```

## Status line shows No active decklist before decklist is created

```scrut
$ printf 'decklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
No active decklist
deckslots> Goodbye.
```
