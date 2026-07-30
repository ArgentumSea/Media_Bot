"""Хендлер для обработки ссылок на посты."""
import logging
import re
from pathlib import Path

from aiogram import Router, Bot, F
from aiogram.types import Message, FSInputFile

from config import TEMP_DIR
from services.downloader import download_from_url
from services.gemini import GeminiService
from services.media import check_size_limit, cleanup_file, get_file_size_mb

router = Router()
gemini = GeminiService()

URL_PATTERN = re.compile(
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*", flags=re.IGNORECASE
)

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".m4a", ".ogg", ".wav", ".aac"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

QUOTA_MSG = ("⚠️ <b>Дневная квота Gemini исчерпана.</b>

Все доступные модели достигли лимита запросов.
Подожди до завтра — квота сбрасывается в 00:00 UTC.")


@router.message(F.text)
async def handle_text_with_links(message: Message, bot: Bot) -> None:
    if not message.text:
        return

    urls = URL_PATTERN.findall(message.text)
    if not urls:
        return

    url = urls[0]
    processing_msg = await message.answer("⏳ Скачиваю контент по ссылке...")

    file_path: Path | None = None
    try:
        file_path, description, title = await download_from_url(url)

        if file_path is None:
            await processing_msg.edit_text(
                "❌ Не удалось скачать контент. Проверь ссылку или попробуй другой сервис."
            )
            return

        if not check_size_limit(file_path):
            size_mb = get_file_size_mb(file_path)
            await processing_msg.edit_text(
                "⚠️ Файл слишком большой (" + f"{size_mb:.1f}" + " МБ). "
                "Лимит Telegram — 50 МБ. Обработка отменена."
            )
            return

        await processing_msg.edit_text("📤 Отправляю медиафайл в чат...")
        ext = file_path.suffix.lower()

        caption = title or "Контент по ссылке"
        if description:
            caption = caption + "

" + description[:500]

        media_file = FSInputFile(path=str(file_path))

        if ext in VIDEO_EXTS:
            await message.answer_video(video=media_file, caption=caption[:1024])
        elif ext in AUDIO_EXTS:
            await message.answer_audio(audio=media_file, caption=caption[:1024])
        elif ext in IMAGE_EXTS:
            await message.answer_photo(photo=media_file, caption=caption[:1024])
        else:
            await message.answer_document(document=media_file, caption=caption[:1024])

        await processing_msg.edit_text("🧠 Анализирую контент через Gemini...")
        result = await gemini.analyze(file_path, text_context=description or title or "")

        if result is None:
            await message.answer(
                "❌ Не удалось проанализировать контент. "
                "Возможно, файл не поддерживается или все модели недоступны."
            )
            return

        if result.get("_quota_exceeded"):
            await message.answer(QUOTA_MSG)
            return

        await processing_msg.delete()

        await message.answer("📝 <b>Конспект:</b>

" + result["summary"])
        await message.answer("📌 <b>Резюме:</b>

" + result["resume"])

        links = result["links"]
        if links:
            links_text = "
".join(f"• {link}" for link in links)
            await message.answer("🔗 <b>Упомянутые ресурсы:</b>

" + links_text)

    except Exception as exc:
        logger.exception("Ошибка при обработке ссылки %s", url)
        await message.answer(
            "❌ Произошла ошибка при обработке. Проверь логи сервера."
        )
    finally:
        if file_path:
            cleanup_file(file_path)
