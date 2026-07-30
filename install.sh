#!/bin/bash
set -e

# ============================================================================
# InstaBot — One-command deploy script for Ubuntu/Debian VPS (root)
# ============================================================================
# Использование (одной строкой на VPS):
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/ArgentumSea/Media_Bot/main/install.sh)"
#
# Или скачай и запусти:
#   wget https://raw.githubusercontent.com/ArgentumSea/Media_Bot/main/install.sh
#   bash install.sh
# ============================================================================

REPO_URL="${REPO_URL:-https://github.com/ArgentumSea/Media_Bot.git}"
INSTALL_DIR="${INSTALL_DIR:-/root/instabot}"
SERVICE_NAME="instabot"

echo "=========================================="
echo "  InstaBot — Автоматический деплой"
echo "=========================================="
echo ""
echo "Репозиторий: $REPO_URL"
echo "Папка:       $INSTALL_DIR"
echo ""

# ─── 1. Обновление системы ─────────────────────────────────────────────────
echo "[1/8] Обновление пакетов..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git ffmpeg

# ─── 2. Клонирование репозитория ───────────────────────────────────────────
echo "[2/8] Клонирование репозитория..."
if [ -d "$INSTALL_DIR" ]; then
    echo "      Папка $INSTALL_DIR уже существует. Удаляем..."
    rm -rf "$INSTALL_DIR"
fi
git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# ─── 3. Создание виртуального окружения ────────────────────────────────────
echo "[3/8] Создание Python-окружения..."
python3 -m venv venv
source venv/bin/activate

# ─── 4. Установка зависимостей ─────────────────────────────────────────────
echo "[4/8] Установка Python-зависимостей..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# ─── 5. Создание .env из шаблона ───────────────────────────────────────────
echo "[5/8] Создание файла конфигурации .env..."
if [ ! -f .env ]; then
    cp .env.example .env
fi

# ─── 6. Создание папки temp ────────────────────────────────────────────────
echo "[6/8] Создание временной папки..."
mkdir -p temp

# ─── 7. Установка systemd-сервиса ──────────────────────────────────────────
echo "[7/8] Настройка systemd-сервиса..."

cat > /etc/systemd/system/$SERVICE_NAME.service << 'EOF'
[Unit]
Description=InstaBot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/instabot
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/instabot/venv/bin/python /root/instabot/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE_NAME

# ─── 8. Финальное сообщение ────────────────────────────────────────────────
echo ""
echo "=========================================="
echo "  ✅ Деплой завершён!"
echo "=========================================="
echo ""
echo "⚠️  ВАЖНО: Перед запуском нужно вставить токены!"
echo ""
echo "Шаг 1. Открой файл конфигурации:"
echo "       nano $INSTALL_DIR/.env"
echo ""
echo "Шаг 2. Замени плейсхолдеры на реальные значения:"
echo "       BOT_TOKEN=123456789:ABC...        ← от @BotFather"
echo "       GEMINI_API_KEY=AIzaSy...          ← от aistudio.google.com"
echo ""
echo "Шаг 3. Сохрани (Ctrl+O, Enter, Ctrl+X) и запусти:"
echo "       systemctl start $SERVICE_NAME"
echo ""
echo "Команды управления:"
echo "       systemctl status $SERVICE_NAME"
echo "       journalctl -u $SERVICE_NAME -f"
echo "       systemctl restart $SERVICE_NAME"
echo "       systemctl stop $SERVICE_NAME"
echo ""

read -p "Открыть .env в редакторе nano прямо сейчас? [Y/n]: " answer
if [ -z "$answer" ] || [ "$answer" = "Y" ] || [ "$answer" = "y" ]; then
    nano "$INSTALL_DIR/.env"
    echo ""
    read -p "Запустить бота сейчас? [Y/n]: " start_answer
    if [ -z "$start_answer" ] || [ "$start_answer" = "Y" ] || [ "$start_answer" = "y" ]; then
        systemctl start $SERVICE_NAME
        echo ""
        echo "🚀 Бот запущен! Проверь статус:"
        echo "   journalctl -u $SERVICE_NAME -f"
    else
        echo ""
        echo "⏸️  Запуск отложен. Когда будешь готов:"
        echo "   systemctl start $SERVICE_NAME"
    fi
else
    echo ""
    echo "⏸️  Не забудь отредактировать .env перед запуском!"
fi
