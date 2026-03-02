#!/bin/bash
# Автоматический деплой на Render.com

set -e

echo "============================================================"
echo "    🚀 Деплой Recruitment System на Render.com"
echo "============================================================"
echo ""

# Проверка Git
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "❌ Это не Git репозиторий!"
    exit 1
fi

# Проверка наличия render.yaml
if [ ! -f render.yaml ]; then
    echo "❌ Файл render.yaml не найден!"
    exit 1
fi

# Commit всех изменений
echo "📦 Фиксация изменений..."
git add -A
git commit -m "Deploy to Render: $(date '+%Y-%m-%d %H:%M:%S')" || echo "Нет изменений"

# Push на GitHub
echo "🚀 Отправка на GitHub..."
git push origin main

echo ""
echo "============================================================"
echo "    ✅ Код отправлен на GitHub!"
echo "============================================================"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Откройте https://render.com"
echo "2. Войдите через GitHub"
echo "3. Dashboard → New + → Blueprint"
echo "4. Выберите репозиторий: xCTPEJIOKx/recruit_bot"
echo "5. Нажмите Connect"
echo ""
echo "🔧 Переменные окружения (добавьте в Render):"
echo "────────────────────────────────────────────────────────"
echo "TELEGRAM_BOT_TOKEN=8546310725:AAGkqmkjFp_DfMFKqA75Q0IXV8xuEU3JaNA"
echo "TELEGRAM_ADMIN_CHAT_ID=819222276"
echo "AVITO_LOGIN=+79538765405"
echo "AVITO_PASSWORD=CTPEJIOK77z."
echo "VOXIMPLANT_ACCOUNT_ID=54675"
echo "VOXIMPLANT_API_KEY=486ba90d76807592a376b8fb355d8fb84802c8413c61afc657f73e69d3c0665e"
echo "DATABASE_PATH=/opt/render/project/src/data/recruitment.db"
echo "ORCHESTRATOR_PORT=10000"
echo "LOG_LEVEL=INFO"
echo "DEBUG=false"
echo "────────────────────────────────────────────────────────"
echo ""
echo "💾 Не забудьте добавить Disk:"
echo "   Mount Path: /opt/render/project/src/data"
echo "   Size: 1 GB"
echo ""
echo "📖 Полная инструкция: docs/DEPLOY_RENDER_STEPBYSTEP.md"
echo "============================================================"
