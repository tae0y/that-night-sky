"""Tests for thatnightsky.logging_setup."""

import logging
import time
from logging.handlers import TimedRotatingFileHandler

from thatnightsky.logging_setup import configure_access_logger


def _reset_logger():
    logger = logging.getLogger("thatnightsky.access")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def test_configure_access_logger_writes_to_file(tmp_path):
    _reset_logger()
    logger = configure_access_logger(tmp_path)
    logger.info("hello")
    for handler in logger.handlers:
        handler.flush()

    log_file = tmp_path / "access.log"
    assert log_file.exists()
    assert "hello" in log_file.read_text(encoding="utf-8")


def test_configure_access_logger_keeps_backup_count_at_six(tmp_path):
    _reset_logger()
    logger = configure_access_logger(tmp_path)
    handler = next(
        h for h in logger.handlers if isinstance(h, TimedRotatingFileHandler)
    )
    assert handler.backupCount == 6


def test_configure_access_logger_prunes_backups_older_than_7_days(tmp_path):
    stale = tmp_path / "access.log.2020-01-01"
    stale.write_text("old", encoding="utf-8")
    old_time = time.time() - 8 * 86400
    import os

    os.utime(stale, (old_time, old_time))

    fresh = tmp_path / "access.log.2099-01-01"
    fresh.write_text("new", encoding="utf-8")

    _reset_logger()
    configure_access_logger(tmp_path)

    assert not stale.exists()
    assert fresh.exists()
