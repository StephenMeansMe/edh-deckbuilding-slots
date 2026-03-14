"""CliRunner-based functional tests replacing scrut tests in tests/functional/.

These tests use click.testing.CliRunner to invoke the REPL in-process,
avoiding the need for the scrut binary or subprocess spawning.  This makes
the suite runnable in any environment that has the Python dependencies
installed, including cloud-based Claude Code deployments.
"""

from pathlib import Path

from click.testing import CliRunner

from deckslots.cli import main

# Fixture files used by import/move/delete tests (mirrors $TESTDIR in scrut).
TESTDIR = Path(__file__).parent / "functional"


def _run(
    commands: str,
    state_home: Path,
    data_home: Path | None = None,
    cache_home: Path | None = None,
) -> str:
    """Invoke the deckslots REPL in-process and return captured stdout."""
    env: dict[str, str] = {"XDG_STATE_HOME": str(state_home)}
    if data_home is not None:
        env["XDG_DATA_HOME"] = str(data_home)
    if cache_home is not None:
        env["XDG_CACHE_HOME"] = str(cache_home)
    runner = CliRunner(mix_stderr=False, env=env)
    result = runner.invoke(main, input=commands)
    return result.output


# ---------------------------------------------------------------------------
# 01-startup.md
# ---------------------------------------------------------------------------


class TestStartup:
    def test_eof_exits_cleanly(self, tmp_path):
        out = _run("", tmp_path)
        assert out == "deckslots> Welcome to deckslots.\ndeckslots> Goodbye.\n"
