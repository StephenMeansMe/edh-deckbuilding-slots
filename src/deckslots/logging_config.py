import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(level: str | None = None) -> None:
    level = level or os.environ.get("DECKSLOTS_LOG_LEVEL")
    if not level:
        return
    logger = logging.getLogger("deckslots")
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(logging.Formatter("%(name)s %(levelname)s: %(message)s"))
    logger.addHandler(sh)
    log_dir = Path.home() / ".local" / "share" / "deckslots"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(log_dir / "debug.log", maxBytes=1_000_000, backupCount=3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    )
    logger.addHandler(fh)
