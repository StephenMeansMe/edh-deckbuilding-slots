import logging
import sys

import click

from deckslots.cli.commands import (
    Session,
    dispatch,
    handle_category_rename,
    handle_decklist_rename,
    handle_help,
    register_all_handlers,
    validate_category_rename,
    validate_decklist_rename,
    validate_template_save,
)
from deckslots.cli.parser import parse_command
from deckslots.cli.status import render_status_line
from deckslots.config import get_storage_backend, is_validation_enabled
from deckslots.logging_config import setup_logging
from deckslots.storage import PlaintextRepository, SqliteRepository
from deckslots.templates import user_template_exists

_logger = logging.getLogger("deckslots.cli.repl")


def _load_scryfall_index(session: Session) -> None:
    """Load the Scryfall index into *session* from the local cache if available.

    If validation is disabled via config, or the cache is absent and stdin is
    not a tty (non-interactive), silently skips.  In interactive mode with no
    cache the user is prompted once to download it.
    """
    from deckslots.scryfall import (
        download_oracle_cards,
        get_cache_path,
        is_cache_stale,
        load_index_from_cache,
    )

    if not is_validation_enabled():
        return

    cache_path = get_cache_path()

    if not is_cache_stale(cache_path):
        index = load_index_from_cache(cache_path)
        if index is not None:
            session.scryfall_index = index
            _logger.debug("Scryfall index loaded from cache (%d entries)", len(index))
            return

    # Cache is absent or stale.  Only prompt in interactive mode.
    if not sys.stdin.isatty():
        return

    try:
        if not click.confirm(
            "Scryfall card database is missing or outdated. Download now?",
            default=False,
        ):
            click.echo("Skipping download. Card validation disabled for this session.")
            return
    except (EOFError, KeyboardInterrupt):
        return

    click.echo("Downloading Scryfall oracle_cards… ", nl=False)
    try:
        download_oracle_cards(cache_path)
        index = load_index_from_cache(cache_path)
        if index is not None:
            session.scryfall_index = index
            click.echo(f"Done ({len(index)} cards loaded).")
        else:
            click.echo("Download succeeded but index could not be loaded.")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Download failed: {exc}")


def _build_repository():
    backend = get_storage_backend()
    if backend == "sqlite":
        return SqliteRepository()
    return PlaintextRepository()


def run_repl() -> None:
    """Start the deckslots interactive REPL."""
    setup_logging()
    session = Session(repository=_build_repository())
    registry = register_all_handlers(session)

    summaries = session.repository.list()
    if summaries:
        latest = summaries[0]
        try:
            session.decklist = session.repository.load(latest.id)
            click.echo(f"Resumed '{session.decklist.name}'.")
            click.echo(render_status_line(session, is_validation_enabled()))
        except (OSError, ValueError, KeyError) as e:
            _logger.warning("Save file load failed, entering recovery: %s", e)
            click.echo(f"Warning: could not load save file: {e}.")
            click.echo("Options:")
            click.echo("  discard — delete the save file and start fresh")
            click.echo("  exit    — quit so you can inspect the file manually")
            while True:
                click.echo("deckslots(recovery)> ", nl=False)
                try:
                    choice = input().strip().lower()
                except (EOFError, KeyboardInterrupt):
                    click.echo("Goodbye.")
                    return
                if choice == "discard":
                    session.repository.delete(latest.id)
                    click.echo("Save file deleted. Starting fresh.")
                    break
                elif choice == "exit":
                    click.echo("Goodbye.")
                    return

    _load_scryfall_index(session)

    click.echo("deckslots> Welcome to deckslots.")
    try:
        while True:
            line = input("deckslots> ")
            parsed = parse_command(line)
            if parsed.kind == "builtin" and parsed.builtin in ("quit", "exit"):
                break
            if parsed.kind == "builtin" and parsed.builtin == "help":
                click.echo(handle_help())
                continue
            if parsed.kind == "empty":
                continue
            if parsed.kind == "object_verb":
                if parsed.verb == "rename":
                    if parsed.obj == "decklist":
                        error = validate_decklist_rename(session)
                        if error:
                            click.echo(error)
                            continue
                        new_name = input("New name: ").strip()
                        if not new_name:
                            click.echo("Name cannot be empty.")
                            continue
                        result = handle_decklist_rename(session, new_name)
                    elif parsed.obj == "category":
                        old_name = " ".join(parsed.args)
                        error = validate_category_rename(session, old_name)
                        if error:
                            click.echo(error)
                            continue
                        new_name = input("New name: ").strip()
                        if not new_name:
                            click.echo("Name cannot be empty.")
                            continue
                        result = handle_category_rename(session, old_name, new_name)
                    else:
                        result = dispatch(parsed, registry)
                elif parsed.verb == "save" and parsed.obj == "template":
                    name = " ".join(parsed.args)
                    error = validate_template_save(session, name)
                    if error:
                        click.echo(error)
                        continue
                    if user_template_exists(name):
                        if not click.confirm(
                            f"Template '{name}' already exists. Overwrite?",
                            default=False,
                        ):
                            click.echo("Aborted.")
                            continue
                    result = dispatch(parsed, registry)
                else:
                    result = dispatch(parsed, registry)
                warnings: list[str] = []
                if (
                    session.decklist is not None
                    and "uncategorized" in session.decklist.categories
                    and session.decklist.categories["uncategorized"].filled > 0
                ):
                    n = session.decklist.categories["uncategorized"].filled
                    warnings.append(
                        f"Warning: {n} card(s) in Uncategorized. "
                        "Assign them to categories before finalizing "
                        "your decklist."
                    )
                if (
                    session.decklist is not None
                    and session.decklist.commander_overcrowded
                ):
                    warnings.append(
                        "Warning: Commander has more cards than enabled modes allow. "
                        "Run 'decklist enable-partners' or "
                        "'decklist enable-background', "
                        "or use 'card move' to reassign the extra cards."
                    )
                if (
                    session.decklist is not None
                    and session.decklist.companion_slot_empty
                    and not (
                        parsed.obj == "decklist" and parsed.verb == "enable-companion"
                    )
                ):
                    warnings.append(
                        "Warning: Companion slot is empty. "
                        "Add a companion with 'card add Companion <card name>'."
                    )
                for w in reversed(warnings):
                    click.echo(click.style(w, fg="yellow", bold=True))
                click.echo(result)
                click.echo(render_status_line(session, is_validation_enabled()))
                continue
            if parsed.kind == "unknown":
                click.echo(f"Unknown command: {parsed.raw}")
    except (EOFError, KeyboardInterrupt):
        pass
    click.echo("Goodbye.")
