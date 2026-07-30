"""Сервис анализа контента через Google Gemini API."""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODELS

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Проанализируй предоставленный медиафайл и текстовый контекст.

Требования:
1. НЕ добавляй своё мнение. НЕ выдумывай факты, которых нет в контенте.
2. НЕ разбавляй текст своими комментариями.
3. Информация должна быть точной и основана только на содержании файла.

Ответ строго в формате JSON:
{
  "summary": "структурированный конспект содержания файла",
  "resume": "краткое резюме, выделяющее суть (3-5 предложений)",
  "links": ["упомянутые ссылки и ресурсы, если есть. Иначе пустой массив"]
}"""

# Ошибки, при которых пробуем fallback-модель
RETRYABLE_ERRORS = ("429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "quota")


class GeminiService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    async def analyze(self, file_path: Path, text_context: str = "") -> Optional[Dict[str, str]]:
        # Загружаем файл (один раз для всех моделей)
        uploaded_file = await self.client.aio.files.upload(file=str(file_path))
        logger.info("Файл загружен в Gemini: %s", uploaded_file.name)

        # Ждём ACTIVE
        max_wait = 60
        waited = 0
        while uploaded_file.state.name != "ACTIVE" and waited < max_wait:
            await asyncio.sleep(2)
            waited += 2
            uploaded_file = await self.client.aio.files.get(name=uploaded_file.name)
            logger.info("Состояние файла: %s (ждём %d сек)", uploaded_file.state.name, waited)

        if uploaded_file.state.name != "ACTIVE":
            logger.error("Файл не стал ACTIVE за %d секунд", max_wait)
            return None

        contents = [uploaded_file]
        if text_context.strip():
            contents.append("Контекст поста:
" + text_context)
        contents.append(ANALYSIS_PROMPT)

        # Пробуем модели по очереди: основная → fallback
        models_to_try = [GEMINI_MODEL] + GEMINI_FALLBACK_MODELS
        last_error = ""

        for model in models_to_try:
            for attempt in range(1, 4):
                try:
                    logger.info("Запрос к модели %s (попытка %d/3)", model, attempt)
                    response = await self.client.aio.models.generate_content(
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                        ),
                    )

                    if not response.text:
                        logger.warning("Модель %s вернула пустой ответ", model)
                        break  # Пробуем следующую модель

                    result = json.loads(response.text)
                    return {
                        "summary": result.get("summary", "—"),
                        "resume": result.get("resume", "—"),
                        "links": result.get("links", []),
                    }

                except Exception as exc:
                    err_str = str(exc)
                    last_error = err_str
                    if any(code in err_str for code in RETRYABLE_ERRORS):
                        logger.warning("Модель %s перегружена (попытка %d/3): %s", model, attempt, err_str)
                        if attempt < 3:
                            await asyncio.sleep(5)
                            continue
                    # Неперехватываемая ошибка — пробуем следующую модель
                    logger.error("Модель %s не сработала: %s", model, err_str)
                    break

        # Все модели исчерпаны
        if "quota" in last_error.lower() or "429" in last_error:
            logger.error("Все модели исчерпали квоту")
            return {"_quota_exceeded": True}

        logger.error("Все модели недоступны. Последняя ошибка: %s", last_error)
        return None
