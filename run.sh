#!/bin/bash
# Скрипт запуска системы рекрутинговых агентов

cd "$(dirname "$0")"

# Проверка .env
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "   Запустите: ./install.sh"
    exit 1
fi

# Проверка Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama не найден. Запуск без ИИ..."
fi

# Запуск
echo "🤖 Запуск системы рекрутинговых агентов..."
echo ""
python3 main.py "$@"
