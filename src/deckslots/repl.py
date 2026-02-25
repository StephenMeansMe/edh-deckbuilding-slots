from deckslots.cli import parse_command
from deckslots.commands import Session, dispatch, handle_help, register_all_handlers


def run_repl():
    """Start the deckslots interactive REPL."""
    session = Session()
    registry = register_all_handlers(session)
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
