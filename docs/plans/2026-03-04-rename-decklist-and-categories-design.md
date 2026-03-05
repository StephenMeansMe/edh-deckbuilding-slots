# Design: Rename Decklist and Categories (US-007)

## User-Facing Behavior

| Command | Interaction | Success output |
|---|---|---|
| `decklist rename` | Prompts `New name: ` | `Renamed decklist to '<new-name>'.` |
| `category rename <old>` | Prompts `New name: ` | `Renamed category '<old>' to '<new>'.` |

Errors returned before prompting:
- No active decklist → `No active decklist. Use 'decklist create <name>' first.`
- `category rename` with no args → `Usage: category rename <name>`
- Category not found → `Category '<name>' not found.`
- Category is fixed → `Cannot rename fixed category '<name>'.`

After prompting:
- Empty new name → `Name cannot be empty.`
- Conflicting new name → `Category '<name>' already exists.`

## Architecture

### REPL (repl.py)
Intercepts `parsed.verb == "rename"` before dispatch:
1. Calls `validate_*_rename()` — if error, print and continue
2. Calls `input("New name: ")` to read new name
3. If empty, print "Name cannot be empty." and continue
4. Calls `handle_*_rename()` and prints result

### Commands (commands.py)
Four new public functions (not in dispatch registry):
- `validate_decklist_rename(session) -> str | None`
- `validate_category_rename(session, old_name) -> str | None`
- `handle_decklist_rename(session, new_name) -> str`
- `handle_category_rename(session, old_name, new_name) -> str`

### Models (models.py)
Two new methods on `Decklist`:
- `rename(new_name)` — sets `self.name = new_name`
- `rename_category(old_name, new_name)` — updates key and display name

## Testing Strategy
- pytest: model methods and command handlers
- scrut: full REPL interaction (two-phase prompt, errors, save/load round-trip)
