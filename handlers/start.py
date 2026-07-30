"""Хендлер команды /start."""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

WELCOME_TEXT = """👋 Привет! Я бот для анализа медиаконтента.

Отправь мне:
• <b>Ссылку</b> на пост (Instagram, Threads, YouTube, TikTok, X/Twitter и др.) — я скачаю контент и сделаю конспект.
• <b>Медиафайл</b> (фото, видео, аудио) — я проанализирую его и выдам конспект, резюме и упомянутые ссылки.

⚠️ Лимит на загрузку файлов: <b>50 МБ</b>."""


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)
