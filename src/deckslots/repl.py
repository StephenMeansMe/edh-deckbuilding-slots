from deckslots.cli import parse_command


def run_repl():
    """Start the deckslots REPL. Rejects all input until commands are implemented."""
    print("deckslots> Welcome to deckslots.")
    try:
        while True:
            line = input("deckslots> ")
            parsed = parse_command(line)
            if parsed.name == "quit":
                break
            if not parsed.known:
                print(f"Unknown command: {line}")
    except (EOFError, KeyboardInterrupt):
        pass
    print("Goodbye.")
