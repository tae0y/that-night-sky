"""Access-log configuration: a time-based rotating file log that guarantees a
7-day retention window regardless of request volume (unlike Docker's
size-based json-file driver, which can retain logs far longer under low
traffic — see docker/docker-compose.yml)."""

from __future__ import annotations

import logging
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_LOGGER_NAME = "thatnightsky.access"
_RETENTION_DAYS = 7
# backupCount=6 rotated files + the active file = 7 days of coverage.
_BACKUP_COUNT = _RETENTION_DAYS - 1


def _prune_stale_backups(log_dir: Path) -> None:
    """Delete rotated backups older than the retention window.

    TimedRotatingFileHandler only rotates (and prunes) on the next emitted
    record after midnight, so an idle app can leave stale backups around
    past 7 days. This sweep runs once at startup as a backstop.
    """
    cutoff = time.time() - _RETENTION_DAYS * 86400
    for backup in log_dir.glob("access.log.*"):
        if backup.stat().st_mtime < cutoff:
            backup.unlink()


def configure_access_logger(log_dir: Path) -> logging.Logger:
    """Configure and return the access logger, writing to log_dir/access.log."""
    log_dir.mkdir(parents=True, exist_ok=True)
    _prune_stale_backups(log_dir)

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
        handler = TimedRotatingFileHandler(
            filename=log_dir / "access.log",
            when="midnight",
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)

    return logger
