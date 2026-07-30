# MediaBot — Анализатор медиаконтента

Личный Telegram-бот для скачивания постов и анализа медиафайлов через Google Gemini.

## Возможности

- Скачивание контента по ссылкам (Instagram, YouTube, TikTok и других сервисов через yt-dlp)
- Обработка входящих медиафайлов (фото, видео, аудио, голосовые, документы)
- Автоматическое создание структурированного конспекта
- Краткое резюме с выделением сути
- Извлечение всех упомянутых ссылок и ресурсов
- Проверка лимита Telegram (50 МБ) — при превышении задача отменяется

## Стек

- Python 3.10+
- aiogram 3.x
- yt-dlp
- Google Gemini API (google-genai)
- python-dotenv

## Установка (локально)

```bash
git clone <repo>
cd instabot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируй .env — вставь BOT_TOKEN и GEMINI_API_KEY
python main.py
```

## Получение GEMINI_API_KEY

1. Перейди на https://aistudio.google.com/app/apikey
2. Нажми "Create API key"
3. Скопируй ключ в `.env`

## Лимиты

- Telegram: бот не может отправлять файлы больше 50 МБ
- Gemini Free Tier: ~60 запросов в минуту (RPM) для Flash-модели
