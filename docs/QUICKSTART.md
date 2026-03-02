# 🚀 Quick Start

## Установка за 5 минут

```bash
# 1. Клонирование и установка
cd /home/hp/recruitment_agents
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Настройка
cp .env.example .env
nano .env  # Добавить TELEGRAM_BOT_TOKEN

# 3. Запуск
python -m common.init_db
python scripts/create_vacancies.py
python run.py
```

## Проверка работы

```bash
# Статус системы
curl http://localhost:8000/status

# Dashboard
open http://localhost:8000/dashboard

# Telegram бот
open https://t.me/YourBot
```

## Команды

| Команда | Описание |
|---------|----------|
| `python run.py` | Запуск всех агентов |
| `python -m common.init_db` | Инициализация БД |
| `python scripts/create_vacancies.py` | Создание тестовых вакансий |
| `python -m orchestrator.orchestrator` | Запуск оркестратора |
| `python -m telegram_bot.bot` | Запуск Telegram бота |
| `python -m avito_agent.avito_browser_agent` | Запуск Avito агента |

## Доступы

- **Dashboard:** http://localhost:8000/dashboard
- **API:** http://localhost:8000/docs
- **Telegram Bot:** @YourBot
