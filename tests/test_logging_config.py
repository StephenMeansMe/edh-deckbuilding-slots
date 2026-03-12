import logging

from deckslots.logging_config import setup_logging


def test_setup_logging_silent_when_env_var_not_set(monkeypatch):
    monkeypatch.delenv("DECKSLOTS_LOG_LEVEL", raising=False)
    logger = logging.getLogger("deckslots")
    logger.handlers.clear()
    setup_logging()
    assert logger.handlers == []
