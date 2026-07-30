"""Вспомогательные функции для работы с медиафайлами."""
import logging
import os
from pathlib import Path

from config import MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)


def get_file_size_mb(path: Path) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def check_size_limit(path: Path) -> bool:
    return os.path.getsize(path) <= MAX_FILE_SIZE_BYTES


def cleanup_file(path: Path) -> None:
    try:
        if path.exists():
            os.remove(path)
            logger.info("Удалён временный файл: %s", path)
    except OSError as exc:
        logger.error("Не удалось удалить файл %s: %s", path, exc)
