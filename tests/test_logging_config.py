import logging
from unittest.mock import patch

from deckslots.logging_config import setup_logging


def test_setup_logging_silent_when_env_var_not_set(monkeypatch):
    monkeypatch.delenv("DECKSLOTS_LOG_LEVEL", raising=False)
    logger = logging.getLogger("deckslots")
    logger.handlers.clear()
    setup_logging()
    assert logger.handlers == []


def test_setup_logging_adds_handlers_when_env_set(monkeypatch, tmp_path):
    monkeypatch.setenv("DECKSLOTS_LOG_LEVEL", "DEBUG")
    logger = logging.getLogger("deckslots")
    logger.handlers.clear()
    with patch("deckslots.logging_config.Path.home", return_value=tmp_path):
        setup_logging()
    assert len(logger.handlers) == 2
    logger.handlers.clear()
