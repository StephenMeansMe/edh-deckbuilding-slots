def run_repl():
    """Start the deckslots REPL. Rejects all input until commands are implemented."""
    print("deckslots> Welcome to deckslots.")
    try:
        while True:
            line = input("deckslots> ")
            print(f"Unknown command: {line}")
    except (EOFError, KeyboardInterrupt):
        pass
    print("Goodbye.")
