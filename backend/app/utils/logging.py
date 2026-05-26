"""Structured logging configuration."""

import logging
import sys
from typing import Any

from app.config import settings


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class PipelineLogger:
    """Collects stage-level logs for API responses."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def log(self, stage: str, level: str, message: str, **extra: Any) -> None:
        entry = {"stage": stage, "level": level, "message": message, **extra}
        self.entries.append(entry)
        logger = get_logger(f"pipeline.{stage}")
        getattr(logger, level.lower(), logger.info)(message)

    def extend(self, entries: list[dict[str, Any]]) -> None:
        self.entries.extend(entries)
