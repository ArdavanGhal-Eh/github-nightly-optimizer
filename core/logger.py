"""
Unified Logging Subsystem for GitHub Nightly Optimizer.
Provides structured, thread-safe, UTF-8 compliant console and file logging.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class SafeConsoleHandler(logging.StreamHandler):
    """StreamHandler resilient to Windows console code page issues with Unicode/Persian text."""
    def emit(self, record):
        try:
            msg = self.format(record)
            if hasattr(self.stream, "buffer"):
                self.stream.buffer.write((msg + self.terminator).encode("utf-8", errors="replace"))
                self.stream.buffer.flush()
            else:
                self.stream.write(msg + self.terminator)
                self.flush()
        except Exception:
            self.handleError(record)


def get_logger(name: str = "NightlyOptimizer", log_dir: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console formatter (concise, clear)
    console_format = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    console_handler = SafeConsoleHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (detailed, rotating)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "nightly_optimizer.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_format = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger
