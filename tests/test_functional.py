"""Functional tests for file I/O CLI behaviour.

These tests replace the scrut functional tests in 06-save-load.md,
07-autoload.md, and 08-export.md, which required shell builtins
(printf redirections, test -f, etc.) that scrut cannot reliably execute.

Each test gets its own tmp_path fixture directory for full isolation.
Uses click.testing.CliRunner for in-process invocation (no subprocess).
"""

from pathlib import Path

from click.testing import CliRunner

from deckslots.cli import main


def _run(commands: str, state_home: Path) -> str:
    """Invoke deckslots with piped stdin and return stdout."""
    runner = CliRunner(env={"XDG_STATE_HOME": str(state_home)})
    result = runner.invoke(main, input=commands)
    return result.output


# ---------------------------------------------------------------------------
# Save / Load  (replaces tests/functional/06-save-load.md)
# ---------------------------------------------------------------------------


class TestSaveLoad:
    def test_decklist_save_persists(self, tmp_path):
        out = _run(
            "decklist create TestDeck\ncategory create Ramp 10\ndecklist save\nquit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "deckslots> Saved 'TestDeck'.\n"
            "deckslots> Goodbye.\n"
        )

    def test_decklist_load_restores_saved_state(self, tmp_path):
        out = _run(
            "decklist create TestDeck\n"
            "category create Ramp 10\n"
            "decklist save\n"
            "decklist load\n"
            "decklist show\n"
            "quit\n",
            tmp_path,
        )
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "deckslots> Created category 'Ramp' with 10 slots.\n"
            "deckslots> Saved 'TestDeck'.\n"
            "deckslots> Loaded 'TestDeck'.\n"
            "deckslots> Decklist: TestDeck\n"
            "Total slots: 11 (0 filled)\n"
            "Categories:\n"
            "  Commander: 0/1 slots filled\n"
            "  Basic Lands: 0 slots filled (uncapped)\n"
            "  Ramp: 0/10 slots filled\n"
            "deckslots> Goodbye.\n"
        )

    def test_decklist_save_without_active_decklist_shows_error(self, tmp_path):
        out = _run("decklist save\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "deckslots> Goodbye.\n"
        )

    def test_decklist_load_without_save_file_shows_error(self, tmp_path):
        out = _run("decklist load\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No saved decklist found.\n"
            "deckslots> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# Auto-Load and Recovery Mode  (replaces tests/functional/07-autoload.md)
# ---------------------------------------------------------------------------


def _write_save(state_home: Path, content: str) -> None:
    save_dir = state_home / "deckslots"
    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / "decklist.bak").write_text(content)


class TestAutoload:
    def test_no_resumed_message_when_no_save_file(self, tmp_path):
        out = _run("quit\n", tmp_path)
        assert out == ("deckslots> Welcome to deckslots.\ndeckslots> Goodbye.\n")

    def test_resumed_message_appears_before_welcome(self, tmp_path):
        _write_save(tmp_path, "# My Deck\n\nCommander\n")
        out = _run("quit\n", tmp_path)
        assert out == (
            "Resumed 'My Deck'.\n"
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Goodbye.\n"
        )

    def test_corrupt_save_shows_warning_and_recovery_options(self, tmp_path):
        _write_save(tmp_path, "not a valid save file\n")
        out = _run("exit\n", tmp_path)
        assert out == (
            "Warning: could not load save file: "
            "Save file missing '# <name>' header line..\n"
            "Options:\n"
            "  discard — delete the save file and start fresh\n"
            "  exit    — quit so you can inspect the file manually\n"
            "deckslots(recovery)> Goodbye.\n"
        )

    def test_corrupt_save_discard_continues_to_repl(self, tmp_path):
        _write_save(tmp_path, "not a valid save file\n")
        out = _run("discard\nquit\n", tmp_path)
        assert out == (
            "Warning: could not load save file: "
            "Save file missing '# <name>' header line..\n"
            "Options:\n"
            "  discard — delete the save file and start fresh\n"
            "  exit    — quit so you can inspect the file manually\n"
            "deckslots(recovery)> Save file deleted. Starting fresh.\n"
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Goodbye.\n"
        )

    def test_corrupt_save_file_deleted_after_discard(self, tmp_path):
        bak = tmp_path / "deckslots" / "decklist.bak"
        _write_save(tmp_path, "not a valid save file\n")
        _run("discard\nquit\n", tmp_path)
        assert not bak.exists()

    def test_corrupt_save_exit_quits_program(self, tmp_path):
        _write_save(tmp_path, "not a valid save file\n")
        out = _run("exit\n", tmp_path)
        assert out == (
            "Warning: could not load save file: "
            "Save file missing '# <name>' header line..\n"
            "Options:\n"
            "  discard — delete the save file and start fresh\n"
            "  exit    — quit so you can inspect the file manually\n"
            "deckslots(recovery)> Goodbye.\n"
        )

    def test_corrupt_save_eof_quits_program(self, tmp_path):
        _write_save(tmp_path, "not a valid save file\n")
        out = _run("", tmp_path)
        assert out == (
            "Warning: could not load save file: "
            "Save file missing '# <name>' header line..\n"
            "Options:\n"
            "  discard — delete the save file and start fresh\n"
            "  exit    — quit so you can inspect the file manually\n"
            "deckslots(recovery)> Goodbye.\n"
        )

    def test_corrupt_save_unrecognised_input_repeats_recovery_prompt(self, tmp_path):
        _write_save(tmp_path, "not a valid save file\n")
        out = _run("oops\nexit\n", tmp_path)
        assert out == (
            "Warning: could not load save file: "
            "Save file missing '# <name>' header line..\n"
            "Options:\n"
            "  discard — delete the save file and start fresh\n"
            "  exit    — quit so you can inspect the file manually\n"
            "deckslots(recovery)> deckslots(recovery)> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# Decklist Export  (replaces tests/functional/08-export.md)
# ---------------------------------------------------------------------------


class TestExport:
    def test_export_writes_file_and_prints_repl_output(self, tmp_path):
        export_path = tmp_path / "deck.txt"
        out = _run(
            f"decklist create TestDeck\n"
            f"category create Ramp 2\n"
            f"card add Ramp Sol Ring\n"
            f"card add Ramp Cultivate\n"
            f"decklist export {export_path}\n"
            f"quit\n",
            tmp_path,
        )
        # The "Exported to <path>" line contains a tmp path that varies; skip it.
        # Its exact format is covered by the unit tests in test_commands.py.
        lines = [
            line
            for line in out.splitlines()
            if not line.startswith("deckslots> Exported")
        ]
        assert lines == [
            "deckslots> Welcome to deckslots.",
            "deckslots> Created decklist 'TestDeck'.",
            "deckslots> Created category 'Ramp' with 2 slots.",
            "deckslots> Added 'Sol Ring' to 'Ramp'.",
            "deckslots> Added 'Cultivate' to 'Ramp'.",
            "deckslots> Goodbye.",
        ]

    def test_exported_file_has_commander_and_maindeck_sections(self, tmp_path):
        export_path = tmp_path / "deck.txt"
        _run(
            f"decklist create TestDeck\n"
            f"category create Ramp 2\n"
            f"card add Ramp Sol Ring\n"
            f"card add Ramp Cultivate\n"
            f"decklist export {export_path}\n"
            f"quit\n",
            tmp_path,
        )
        assert export_path.read_text() == (
            "Commander\n\nMaindeck\n1 Cultivate\n1 Sol Ring\n"
        )

    def test_export_with_commander_card_writes_commander_section(self, tmp_path):
        export_path = tmp_path / "deck.txt"
        _run(
            f"decklist create MyDeck\n"
            f"card add Commander Atraxa, Praetors' Voice\n"
            f"decklist export {export_path}\n"
            f"quit\n",
            tmp_path,
        )
        assert export_path.read_text() == (
            "Commander\n1 Atraxa, Praetors' Voice\n\nMaindeck\n"
        )

    def test_export_without_active_decklist_shows_error(self, tmp_path):
        export_path = tmp_path / "deck.txt"
        out = _run(f"decklist export {export_path}\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> No active decklist. Use 'decklist create <name>' first.\n"
            "deckslots> Goodbye.\n"
        )

    def test_export_without_filepath_shows_usage(self, tmp_path):
        out = _run("decklist create TestDeck\ndecklist export\nquit\n", tmp_path)
        assert out == (
            "deckslots> Welcome to deckslots.\n"
            "deckslots> Created decklist 'TestDeck'.\n"
            "deckslots> Usage: decklist export <filepath>\n"
            "deckslots> Goodbye.\n"
        )


# ---------------------------------------------------------------------------
# Commander Overcrowded Warning  (repl.py persistent warning)
# ---------------------------------------------------------------------------


class TestCompanionSlotEmptyWarning:
    """REPL warns when companion mode is enabled but the slot is empty."""

    def test_warning_shown_when_companion_enabled_and_empty(self, tmp_path):
        """Warning shown after enabling companion with no card added."""
        out = _run(
            "decklist create MyDeck\ndecklist enable-companion\ndecklist show\nquit\n",
            tmp_path,
        )
        assert "Warning" in out
        assert "Companion" in out
        assert "empty" in out

    def test_warning_not_shown_when_companion_disabled(self, tmp_path):
        """No companion warning appears when companion mode is off."""
        out = _run(
            "decklist create MyDeck\ndecklist show\nquit\n",
            tmp_path,
        )
        assert "Companion slot is empty" not in out

    def test_warning_not_shown_when_companion_filled(self, tmp_path):
        """No companion warning appears when the companion card is present."""
        out = _run(
            "decklist create MyDeck\n"
            "decklist enable-companion\n"
            "card add Companion Lurrus of the Dream-Den\n"
            "decklist show\n"
            "quit\n",
            tmp_path,
        )
        assert "Companion slot is empty" not in out


class TestCommanderOvercrowdedWarning:
    def test_overcrowded_warning_appears_after_load(self, tmp_path):
        """Warning appears when a loaded save has 2 commanders but no mode enabled."""
        save_content = (
            "# My Deck\n\nCommander\n"
            "1 Cloakwood Hermit\n1 Criminal Past\n\nBasic Lands\n"
        )
        _write_save(tmp_path, save_content)
        out = _run("decklist show\nquit\n", tmp_path)
        assert "Warning" in out
        assert "Commander" in out
        assert "more cards" in out
