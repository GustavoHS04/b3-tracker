from pathlib import Path

import logging
from logging.handlers import RotatingFileHandler

from .config import LOG_DIR, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUPS

def setup_logging(log_file: Path = LOG_FILE) -> None:
    LOG_DIR.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUPS, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console)