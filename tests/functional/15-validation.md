# Scryfall Card Validation

## Setup: create a minimal Scryfall cache in a temp directory

These tests set `XDG_CACHE_HOME` to a subdirectory of `$TMPDIR` containing a
pre-built `deckslots/oracle_cards.json` with a small card index so the app loads
it at startup without hitting the network.

```scrut
$ mkdir -p "$TMPDIR/cache/deckslots" && printf '[{"name":"Sol Ring","legalities":{"commander":"legal"}},{"name":"Oko, Thief of Crowns","legalities":{"commander":"banned"}}]' > "$TMPDIR/cache/deckslots/oracle_cards.json"
```

## Legal card: no validation warning

```scrut
$ printf 'decklist create Test\ncategory create Ramp 10\ncard add Ramp Sol Ring\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" XDG_CACHE_HOME="$TMPDIR/cache" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Test'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Sol Ring' to 'Ramp'.
deckslots> Goodbye.
```

## Unknown card: validation warning (card not found in Scryfall)

```scrut
$ printf 'decklist create Test\ncategory create Ramp 10\ncard add Ramp Mox Opal\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" XDG_CACHE_HOME="$TMPDIR/cache" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Test'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Warning: 'Mox Opal' not found in Scryfall database.
Added 'Mox Opal' to 'Ramp'.
deckslots> Goodbye.
```

## Banned card: validation warning (not Commander-legal)

```scrut
$ printf 'decklist create Test\ncategory create PW 10\ncard add PW Oko, Thief of Crowns\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" XDG_CACHE_HOME="$TMPDIR/cache" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Test'.
deckslots> Created category 'PW' with 10 slots.
deckslots> Warning: 'Oko, Thief of Crowns' is not legal in Commander format.
Added 'Oko, Thief of Crowns' to 'PW'.
deckslots> Goodbye.
```

## Basic lands skip validation even with index present

```scrut
$ printf 'decklist create Test\ncard add Basic Lands Forest\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" XDG_CACHE_HOME="$TMPDIR/cache" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Test'.
deckslots> Added 'Forest' to 'Basic Lands'.
deckslots> Goodbye.
```

## No validation when cache is absent (offline-first, non-interactive)

```scrut
$ mkdir -p "$TMPDIR/nocache"
$ printf 'decklist create Test\ncategory create Ramp 10\ncard add Ramp Gibberish Card\nquit\n' \
>   | XDG_STATE_HOME="$TMPDIR" XDG_CACHE_HOME="$TMPDIR/nocache" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Test'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Added 'Gibberish Card' to 'Ramp'.
deckslots> Goodbye.
```
