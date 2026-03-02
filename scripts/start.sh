#!/bin/bash
# Быстрый старт системы

set -e

echo "🚀 Запуск системы рекрутинговых агентов..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.10+"
    exit 1
fi

echo "✅ Python: $(python3 --version)"

# Создание виртуального окружения (если нет)
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация venv
source venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install -q -r requirements.txt

# Создание директории для данных
mkdir -p data

# Инициализация БД
echo "🗄️  Инициализация базы данных..."
python -m common.init_db

# Проверка .env
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Копируем из .env.example..."
    cp .env.example .env
    echo "📝 Отредактируйте .env и добавьте TELEGRAM_BOT_TOKEN"
fi

echo ""
echo "=========================================="
echo "✅ Система готова к запуску!"
echo "=========================================="
echo ""
echo "📝 Для запуска выполните:"
echo "   python run_all.py"
echo ""
echo "🌐 API будет доступно на: http://localhost:8000"
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo ""
echo "🔑 Не забудьте добавить TELEGRAM_BOT_TOKEN в .env!"
echo "   Получите токен у @BotFather в Telegram"
echo ""
