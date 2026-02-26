# Functional Test Bootstrap

Verifies the CLI binary is reachable before running any test file.
This file is not included automatically — it documents the smoke test.

```scrut
$ printf 'quit\n' | XDG_STATE_HOME="$TMPDIR" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Goodbye.
```
