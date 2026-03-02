#!/bin/bash
# Recruitment System - Быстрый старт
# Используйте этот скрипт для продолжения работы

echo "============================================================"
echo "    Recruitment System - Запуск системы"
echo "============================================================"
echo ""

cd /home/hp/recruitment_agents

# Проверка процессов
echo "📊 Проверка активных процессов..."
ps aux | grep -E "python3.*(orchestrator|telegram_bot|avito_agent|voice_agent|web_dashboard)" | grep -v grep

echo ""
echo "Выберите режим запуска:"
echo "  1. Запустить все компоненты"
echo "  2. Запустить только веб-интерфейс"
echo "  3. Запустить только Telegram бота"
echo "  4. Остановить все компоненты"
echo "  5. Проверить статус"
echo ""
read -p "Ваш выбор (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Запуск всех компонентов..."
        
        # Orchestrator
        echo "  📡 Запуск Orchestrator (порт 8000)..."
        nohup python3 -m orchestrator.orchestrator > /tmp/orch.log 2>&1 &
        sleep 2
        
        # Telegram Bot
        echo "  📱 Запуск Telegram Bot..."
        nohup python3 -m telegram_bot.bot > /tmp/tg.log 2>&1 &
        sleep 2
        
        # Avito Agent
        echo "  📦 Запуск Avito Agent..."
        nohup python3 -m avito_agent.agent > /tmp/avito.log 2>&1 &
        sleep 2
        
        # Voice Agent
        echo "  📞 Запуск Voice Agent..."
        nohup python3 -m voice_agent.voice_agent > /tmp/voice.log 2>&1 &
        sleep 2
        
        # Web Dashboard
        echo "  🌐 Запуск Web Dashboard (порт 8080)..."
        nohup python3 scripts/run_web.py > /tmp/web.log 2>&1 &
        sleep 5
        
        echo ""
        echo "✅ Все компоненты запущены!"
        echo ""
        echo "📡 URLs:"
        echo "   - Dashboard: http://localhost:8080/"
        echo "   - API: http://localhost:8000/"
        echo "   - Telegram Bot: @Recruit2026_bot"
        echo ""
        ;;
        
    2)
        echo ""
        echo "🌐 Запуск веб-интерфейса..."
        nohup python3 scripts/run_web.py > /tmp/web.log 2>&1 &
        sleep 5
        echo "✅ Веб-интерфейс запущен: http://localhost:8080/"
        echo ""
        ;;
        
    3)
        echo ""
        echo "📱 Запуск Telegram бота..."
        nohup python3 -m telegram_bot.bot > /tmp/tg.log 2>&1 &
        sleep 3
        echo "✅ Telegram бот запущен: @Recruit2026_bot"
        echo ""
        ;;
        
    4)
        echo ""
        echo "🛑 Остановка всех компонентов..."
        pkill -f "python3.*orchestrator"
        pkill -f "python3.*telegram_bot"
        pkill -f "python3.*avito_agent"
        pkill -f "python3.*voice_agent"
        pkill -f "python3.*web_dashboard"
        sleep 2
        echo "✅ Все компоненты остановлены"
        echo ""
        ;;
        
    5)
        echo ""
        echo "📊 Статус системы:"
        echo ""
        
        # Проверка Orchestrator
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "  ✅ Orchestrator: работает (порт 8000)"
        else
            echo "  ❌ Orchestrator: не работает"
        fi
        
        # Проверка Web Dashboard
        if curl -s http://localhost:8080/ > /dev/null 2>&1; then
            echo "  ✅ Web Dashboard: работает (порт 8080)"
        else
            echo "  ❌ Web Dashboard: не работает"
        fi
        
        # Проверка Telegram Bot
        if pgrep -f "telegram_bot.bot" > /dev/null; then
            echo "  ✅ Telegram Bot: работает"
        else
            echo "  ❌ Telegram Bot: не работает"
        fi
        
        # Проверка Voice Agent
        if pgrep -f "voice_agent.voice_agent" > /dev/null; then
            echo "  ✅ Voice Agent: работает"
        else
            echo "  ❌ Voice Agent: не работает"
        fi
        
        echo ""
        echo "📈 Статистика:"
        curl -s http://localhost:8000/stats 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  Недоступно"
        echo ""
        ;;
        
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

echo "============================================================"
echo "Для просмотра логов:"
echo "  tail -f /tmp/orch.log    - Orchestrator"
echo "  tail -f /tmp/tg.log      - Telegram Bot"
echo "  tail -f /tmp/voice.log   - Voice Agent"
echo "  tail -f /tmp/web.log     - Web Dashboard"
echo "============================================================"
