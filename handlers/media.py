"""Хендлер для обработки входящих медиафайлов."""
import logging
from pathlib import Path

from aiogram import Router, Bot, F
from aiogram.types import Message

from config import TEMP_DIR
from services.gemini import GeminiService
from services.media import check_size_limit, cleanup_file, get_file_size_mb

router = Router()
gemini = GeminiService()

logger = logging.getLogger(__name__)

QUOTA_MSG = ("⚠️ <b>Дневная квота Gemini исчерпана.</b>

Все доступные модели достигли лимита запросов.
Подожди до завтра — квота сбрасывается в 00:00 UTC.")


@router.message(F.photo | F.video | F.audio | F.voice | F.document)
async def handle_media(message: Message, bot: Bot) -> None:
    file_id: str | None = None
    file_name: str = "media"

    if message.photo:
        file_id = message.photo[-1].file_id
        file_name = f"{message.photo[-1].file_unique_id}.jpg"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or f"{message.video.file_unique_id}.mp4"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or f"{message.audio.file_unique_id}.mp3"
    elif message.voice:
        file_id = message.voice.file_id
        file_name = f"{message.voice.file_unique_id}.ogg"
    elif message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or f"{message.document.file_unique_id}.bin"
    else:
        return

    processing_msg = await message.answer("⏳ Скачиваю файл для анализа...")

    local_path = TEMP_DIR / file_name
    try:
        await bot.download(file_id, destination=str(local_path))

        if not check_size_limit(local_path):
            size_mb = get_file_size_mb(local_path)
            await processing_msg.edit_text(
                "⚠️ Файл слишком большой (" + f"{size_mb:.1f}" + " МБ). "
                "Лимит Telegram — 50 МБ. Обработка отменена."
            )
            return

        await processing_msg.edit_text("🧠 Анализирую контент через Gemini...")
        result = await gemini.analyze(local_path, text_context=message.caption or "")

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
        logger.exception("Ошибка при обработке медиа")
        await message.answer("❌ Произошла ошибка при обработке файла.")
    finally:
        cleanup_file(local_path)
