"""Сервис скачивания контента через yt-dlp."""
import asyncio
import logging
from pathlib import Path
from typing import Tuple, Optional

import yt_dlp

from config import TEMP_DIR, MAX_FILE_SIZE_BYTES

logger = logging.getLogger(__name__)

YDL_OPTS = {
    "outtmpl": str(TEMP_DIR / "%(id)s.%(ext)s"),
    "format": f"best[filesize<{MAX_FILE_SIZE_BYTES // (1024*1024) + 10}M]/best",
    "quiet": True,
    "no_warnings": True,
    "writethumbnail": False,
    "writeinfojson": False,
}


def _download_sync(url: str) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                logger.warning("yt-dlp не вернул info для %s", url)
                return None, None, None

            filename = ydl.prepare_filename(info)
            file_path = Path(filename)

            if not file_path.exists():
                possible = list(TEMP_DIR.glob(f"{info.get('id', '*')}.*"))
                if possible:
                    file_path = possible[0]

            if not file_path.exists():
                logger.warning("Файл не найден после скачивания: %s", filename)
                return None, None, None

            description = info.get("description") or ""
            title = info.get("title") or ""
            return file_path, description, title

    except Exception as exc:
        logger.error("Ошибка при скачивании %s: %s", url, exc)
        return None, None, None


async def download_from_url(url: str) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    return await asyncio.to_thread(_download_sync, url)
