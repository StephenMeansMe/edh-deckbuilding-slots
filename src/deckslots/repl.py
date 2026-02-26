from deckslots.cli import parse_command
from deckslots.commands import (
    Session,
    _get_save_path,
    _parse_save_file,
    dispatch,
    handle_help,
    register_all_handlers,
)


def run_repl():
    """Start the deckslots interactive REPL."""
    session = Session()
    registry = register_all_handlers(session)

    save_path = _get_save_path()
    if save_path.exists():
        try:
            session.decklist = _parse_save_file(str(save_path))
            print(f"Resumed '{session.decklist.name}'.")
        except Exception as e:
            print(f"Warning: could not load save file: {e}.")
            print("Options:")
            print("  discard — delete the save file and start fresh")
            print("  exit    — quit so you can inspect the file manually")
            while True:
                print("deckslots(recovery)> ", end="", flush=True)
                try:
                    choice = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    print("Goodbye.")
                    return
                if choice == "discard":
                    save_path.unlink()
                    print("Save file deleted. Starting fresh.")
                    break
                elif choice == "exit":
                    print("Goodbye.")
                    return

    print("deckslots> Welcome to deckslots.")
    try:
        while True:
            line = input("deckslots> ")
            parsed = parse_command(line)
            if parsed.kind == "builtin" and parsed.builtin in ("quit", "exit"):
                break
            if parsed.kind == "builtin" and parsed.builtin == "help":
                print(handle_help())
                continue
            if parsed.kind == "empty":
                continue
            if parsed.kind == "object_verb":
                result = dispatch(parsed, registry)
                if (
                    session.decklist is not None
                    and "uncategorized" in session.decklist.categories
                    and session.decklist.categories["uncategorized"].filled > 0
                ):
                    n = session.decklist.categories["uncategorized"].filled
                    warning = (
                        f"Warning: {n} card(s) in Uncategorized. "
                        "Assign them to categories before finalizing "
                        "your decklist."
                    )
                    result = f"{warning}\n{result}"
                print(result)
                continue
            if parsed.kind == "unknown":
                print(f"Unknown command: {parsed.raw}")
    except (EOFError, KeyboardInterrupt):
        pass
    print("Goodbye.")
