# Template Commands

## template list shows built-in templates

```scrut
$ printf 'template list\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Templates:
  [built-in] Goldfish Fundamentals — Ramp (10), Card Advantage (10), Targeted Removal (10), Board Wipes (5), Finishers (10), Interaction (5), Threats (15), Utility (5)
deckslots> Goodbye.
```

## template list without active deck still works

```scrut
$ printf 'template list\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Templates:
  [built-in] Goldfish Fundamentals — Ramp (10), Card Advantage (10), Targeted Removal (10), Board Wipes (5), Finishers (10), Interaction (5), Threats (15), Utility (5)
deckslots> Goodbye.
```

## decklist create with valid template applies categories

```scrut
$ printf 'decklist create Aristocrats --template Goldfish Fundamentals\ndecklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'Aristocrats' with template 'Goldfish Fundamentals'.
deckslots> Decklist: Aristocrats
Total slots: 71 (0 filled)
Categories:
  Commander: 0/1 slots filled
  Basic Lands: 0 slots filled (uncapped)
  Ramp: 0/10 slots filled
  Card Advantage: 0/10 slots filled
  Targeted Removal: 0/10 slots filled
  Board Wipes: 0/5 slots filled
  Finishers: 0/10 slots filled
  Interaction: 0/5 slots filled
  Threats: 0/15 slots filled
  Utility: 0/5 slots filled
deckslots> Goodbye.
```

## decklist create with unknown template returns error and does not create deck

```scrut
$ printf 'decklist create MyDeck --template NoSuchTemplate\ndecklist show\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Template 'NoSuchTemplate' not found.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## decklist apply-template applies categories and moves cards

```scrut
$ printf 'decklist create TestDeck\ncategory create Old 5\ncard add Old Sol Ring\ndecklist apply-template Goldfish Fundamentals\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Old' with 5 slots.
deckslots> Added 'Sol Ring' to 'Old'.
deckslots> Warning: 1 card(s) in Uncategorized. Assign them to categories before finalizing your decklist.
Applied template 'Goldfish Fundamentals' to 'TestDeck'. 1 card(s) moved to Uncategorized.
deckslots> Goodbye.
```

## decklist apply-template with unknown template returns error

```scrut
$ printf 'decklist create TestDeck\ndecklist apply-template NoSuchTemplate\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Template 'NoSuchTemplate' not found.
deckslots> Goodbye.
```

## decklist apply-template without active deck returns error

```scrut
$ printf 'decklist apply-template Goldfish Fundamentals\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## template save stores current user categories as a template

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ncategory create Draw 8\ntemplate save My Custom\ntemplate list\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data2" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Created category 'Draw' with 8 slots.
deckslots> Saved template 'My Custom'.
deckslots> Templates:
  [built-in] Goldfish Fundamentals — Ramp (10), Card Advantage (10), Targeted Removal (10), Board Wipes (5), Finishers (10), Interaction (5), Threats (15), Utility (5)
  [user] My Custom — Ramp (10), Draw (8)
deckslots> Goodbye.
```

## template save without active deck returns error

```scrut
$ printf 'template save My Template\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> No active decklist. Use 'decklist create <name>' first.
deckslots> Goodbye.
```

## template export writes template file

```scrut
$ printf 'decklist create TestDeck\ncategory create Ramp 10\ntemplate save ExportMe\ntemplate export ExportMe '$TMPDIR'/exported.tmpl\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data3" uv run deckslots | grep -v "Exported template"
deckslots> Welcome to deckslots.
deckslots> Created decklist 'TestDeck'.
deckslots> Created category 'Ramp' with 10 slots.
deckslots> Saved template 'ExportMe'.
deckslots> Goodbye.
```

## template import loads a template from a file

```scrut
$ printf '# Imported Template\nRamp [12 slots]\n' > "$TMPDIR/imp.tmpl" && printf 'template import '$TMPDIR'/imp.tmpl\ntemplate list\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data4" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> Imported template 'Imported Template'.
deckslots> Templates:
  [built-in] Goldfish Fundamentals — Ramp (10), Card Advantage (10), Targeted Removal (10), Board Wipes (5), Finishers (10), Interaction (5), Threats (15), Utility (5)
  [user] Imported Template — Ramp (12)
deckslots> Goodbye.
```

## template import with nonexistent file returns error

```scrut
$ printf 'template import /nonexistent/path.tmpl\nquit\n' | XDG_STATE_HOME="$TMPDIR" XDG_DATA_HOME="$TMPDIR/data" uv run deckslots
deckslots> Welcome to deckslots.
deckslots> File not found: '/nonexistent/path.tmpl'
deckslots> Goodbye.
```
