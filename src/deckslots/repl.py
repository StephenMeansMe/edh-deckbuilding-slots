import logging

from deckslots.cli import parse_command
from deckslots.commands import (
    Session,
    _get_save_path,
    _parse_save_file,
    dispatch,
    handle_category_rename,
    handle_decklist_rename,
    handle_help,
    register_all_handlers,
    validate_category_rename,
    validate_decklist_rename,
    validate_template_save,
)
from deckslots.logging_config import setup_logging
from deckslots.templates import user_template_exists

_logger = logging.getLogger("deckslots.repl")


def run_repl() -> None:
    """Start the deckslots interactive REPL."""
    setup_logging()
    session = Session()
    registry = register_all_handlers(session)

    save_path = _get_save_path()
    if save_path.exists():
        try:
            session.decklist = _parse_save_file(str(save_path))
            print(f"Resumed '{session.decklist.name}'.")
        except (OSError, ValueError) as e:
            _logger.warning("Save file load failed, entering recovery: %s", e)
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
                if parsed.verb == "rename":
                    if parsed.obj == "decklist":
                        error = validate_decklist_rename(session)
                        if error:
                            print(error)
                            continue
                        new_name = input("New name: ").strip()
                        if not new_name:
                            print("Name cannot be empty.")
                            continue
                        result = handle_decklist_rename(session, new_name)
                    elif parsed.obj == "category":
                        old_name = " ".join(parsed.args)
                        error = validate_category_rename(session, old_name)
                        if error:
                            print(error)
                            continue
                        new_name = input("New name: ").strip()
                        if not new_name:
                            print("Name cannot be empty.")
                            continue
                        result = handle_category_rename(session, old_name, new_name)
                    else:
                        result = dispatch(parsed, registry)
                elif parsed.verb == "save" and parsed.obj == "template":
                    name = " ".join(parsed.args)
                    error = validate_template_save(session, name)
                    if error:
                        print(error)
                        continue
                    if user_template_exists(name):
                        confirm = input(
                            f"Template '{name}' already exists. Overwrite? [y/N]: "
                        ).strip().lower()
                        if confirm != "y":
                            print("Aborted.")
                            continue
                    result = dispatch(parsed, registry)
                else:
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
                if (
                    session.decklist is not None
                    and session.decklist.commander_overcrowded
                ):
                    warning = (
                        "Warning: Commander has more cards than enabled modes allow. "
                        "Run 'decklist enable-partners' or "
                        "'decklist enable-background', "
                        "or use 'card move' to reassign the extra cards."
                    )
                    result = f"{warning}\n{result}"
                if (
                    session.decklist is not None
                    and session.decklist.companion_slot_empty
                    and not (
                        parsed.obj == "decklist"
                        and parsed.verb == "enable-companion"
                    )
                ):
                    warning = (
                        "Warning: Companion slot is empty. "
                        "Add a companion with 'card add Companion <card name>'."
                    )
                    result = f"{warning}\n{result}"
                print(result)
                continue
            if parsed.kind == "unknown":
                print(f"Unknown command: {parsed.raw}")
    except (EOFError, KeyboardInterrupt):
        pass
    print("Goodbye.")
