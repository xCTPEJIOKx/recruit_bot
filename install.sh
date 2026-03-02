#!/bin/bash
# Скрипт автоматической установки системы рекрутинговых агентов

set -e

echo "🚀 Установка системы рекрутинговых агентов..."
echo ""

# Переход в директорию проекта
cd "$(dirname "$0")"

# 1. Проверка Python
echo "📦 Проверка Python..."
python3 --version || { echo "❌ Python 3 не найден!"; exit 1; }

# 2. Установка зависимостей Python
echo "📦 Установка Python зависимостей..."
pip3 install -r requirements.txt --break-system-packages

# 3. Установка Playwright браузеров
echo "📦 Установка браузеров Playwright..."
python3 -m playwright install chromium

# 4. Проверка Ollama
echo "🤖 Проверка Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama уже установлен"
    ollama --version
else
    echo "⚠️ Ollama не найден."
    echo "   Для установки ИИ выполните:"
    echo "   curl -fsSL https://ollama.com/install.sh | bash"
    echo "   ollama pull llama3"
fi

# 5. Создание .env если нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp .env.example .env
    echo "⚠️ Отредактируйте .env и добавьте ваши данные!"
else
    echo "✅ .env уже существует"
fi

# 6. Создание директорий
echo "📁 Создание директорий..."
mkdir -p calls models

# 7. Инициализация БД
echo "🗄️ Инициализация базы данных..."
python3 -c "from core.database import init_db; init_db(); print('✅ БД готова')"

echo ""
echo "=========================================="
echo "✅ Установка завершена!"
echo "=========================================="
echo ""
echo "📝 Следующие шаги:"
echo "   1. Отредактируйте .env файл"
echo "   2. Запустите: ./run.sh"
echo ""
echo "📋 Для получения токена Telegram бота:"
echo "   - Напишите @BotFather в Telegram"
echo "   - Создайте нового бота командой /newbot"
echo ""
