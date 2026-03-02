# 🤖 Recruitment Agents System

Автоматизированная система рекрутинга из 4 агентов с нулевым бюджетом.

## 📋 Архитектура

```
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │  (API + Dashboard)│
                    │  Port: 8000     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Avito Agent    │ │  Voice Agent    │ │  Telegram Bot   │
│  (Публикация +  │ │  (Звонки)       │ │  (Квалификация) │
│   отклики)      │ │  (Voximplant)   │ │  (Aiogram)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Classifieds     │
                    │ Agent           │
                    │ (Доски)         │
                    └─────────────────┘
```

## 🚀 Быстрый старт

### 1. Требования

- Python 3.10+
- Telegram Bot Token (@BotFather)
- Avito аккаунт (для браузерной автоматизации)

### 2. Установка

```bash
cd /home/hp/recruitment_agents

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Зависимости
pip install -r requirements.txt

# Playwright браузеры
playwright install chromium
```

### 3. Настройка

```bash
# Копирование .env
cp .env.example .env

# Редактирование
nano .env
```

**Обязательные переменные:**
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Avito (браузерная автоматизация)
AVITO_LOGIN=+79990000000
AVITO_PASSWORD=your_password

# База данных
DATABASE_PATH=./data/recruitment.db
```

### 4. Запуск

```bash
# Инициализация БД
python -m common.init_db

# Создание вакансий
python scripts/create_vacancies.py

# Запуск всех агентов
python run.py
```

### Запуск через Docker

```bash
docker-compose up -d
```

## 📁 Структура проекта

```
recruitment_agents/
├── common/                 # Общие модули
│   ├── config.py          # Настройки (pydantic)
│   ├── database.py        # Асинхронная БД (aiosqlite)
│   ├── models.py          # Модели данных
│   └── init_db.py         # Инициализация БД
├── avito_agent/           # Avito агент
│   ├── agent.py           # Avito API
│   └── avito_browser_agent.py  # Браузерный агент
├── telegram_bot/          # Telegram бот
│   └── bot.py            # Aiogram бот
├── voice_agent/           # Voice агент
│   └── voice_agent.py    # Voximplant/Twilio
├── classifieds_agent/     # Доски объявлений
│   └── agent.py          # Мультиплатформенный постинг
├── orchestrator/          # Координатор
│   └── orchestrator.py   # FastAPI + Dashboard
├── web_dashboard/         # Веб-интерфейс
│   ├── app.py            # Dashboard API
│   ├── templates/        # Jinja2 шаблоны
│   └── static/           # Статика (Telegram Web App)
├── scripts/               # Скрипты
│   ├── create_vacancies.py
│   ├── create_tunnel.py   # Cloudflare туннель
│   └── avito_oauth.py     # OAuth для Avito
├── docs/                  # Документация
├── data/                  # База данных
├── run.py                 # Запуск всех агентов
├── requirements.txt       # Зависимости
└── .env                   # Конфигурация
```

## 🤖 Агенты

### Avito Agent

**Функционал:**
- Публикация вакансий на Avito
- Мониторинг откликов (каждую минуту)
- Отправка приглашений в Telegram бот
- Сохранение кандидатов в БД

**Режимы работы:**
1. **API** — через Avito OAuth API (требуются токены)
2. **Browser** — браузерная автоматизация (Playwright)

**Запуск:**
```bash
python -m avito_agent.avito_browser_agent
```

### Telegram Bot

**Команды:**
- `/start` — Начало работы
- `/status` — Статус заявки
- `/vacancies` — Список вакансий

**Воронка квалификации:**
1. Имя → 2. Телефон → 3. Опыт → 4. График → 5. Зарплата

**Запуск:**
```bash
python -m telegram_bot.bot
```

### Voice Agent

**Интеграции:**
- Voximplant (основная)
- Twilio (альтернатива)

**Сценарии:**
- Исходящие звонки кандидатам
- Квалификация через голосовой диалог
- Назначение собеседований

**Запуск:**
```bash
python -m voice_agent.voice_agent
```

### Classifieds Agent

**Площадки:**
- Avito, Cian, DomClick, Auto.ru и др.

**Функционал:**
- Автоматический постинг вакансий
- Мультиплатформенная публикация

**Запуск:**
```bash
python -m classifieds_agent.agent
```

### Orchestrator

**API Endpoints:**

| Endpoint | Описание |
|----------|----------|
| `GET /` | Информация о сервисе |
| `GET /health` | Проверка здоровья |
| `GET /status` | Статус всех агентов |
| `GET /dashboard` | Веб-дашборд |
| `GET /candidates` | Список кандидатов |
| `GET /vacancies` | Список вакансий |

**Запуск:**
```bash
python -m orchestrator.orchestrator
```

## 📊 Воронка рекрутинга

```
🆕 Новый → 📞 Связались → ✅ Квалифицирован → 📅 Собеседование → 📋 Offer → 🎉 Принят
```

**Статусы кандидатов:**
- `new` — Новый отклик
- `contacted` — Связались
- `qualified` — Квалифицирован
- `interview` — Назначено собеседование
- `offer` — Предложение сделано
- `hired` — Принят
- `rejected` — Отказ

## 🔧 Конфигурация

### Переменные окружения (.env)

```bash
# Telegram Bot (обязательно)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Avito (для браузерной автоматизации)
AVITO_LOGIN=+79990000000
AVITO_PASSWORD=your_password

# Avito API (опционально)
AVITO_CLIENT_ID=your_client_id
AVITO_CLIENT_SECRET=your_client_secret
AVITO_ACCESS_TOKEN=your_access_token
AVITO_REFRESH_TOKEN=your_refresh_token

# Telephony - Voximplant
VOXIMPLANT_ACCOUNT_ID=54675
VOXIMPLANT_API_KEY=your_api_key
VOXIMPLANT_PHONE_NUMBER=+79990000000

# База данных
DATABASE_PATH=./data/recruitment.db

# Orchestrator
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8000

# Web App URL (для Telegram)
WEBAPP_URL=https://your-domain.com

# Логирование
LOG_LEVEL=INFO
DEBUG=false
```

## 📈 Мониторинг

### Проверка статуса

```bash
# Через API
curl http://localhost:8000/status

# Dashboard
curl http://localhost:8000/dashboard

# Кандидаты с Avito
curl http://localhost:8000/candidates?source=avito
```

### Логи

```bash
# Orchestrator
tail -f /tmp/orchestrator.log

# Avito Agent
tail -f /tmp/avito_browser.log

# Telegram Bot
tail -f /tmp/telegram_bot.log
```

## 🚨 Troubleshooting

### Бот не отвечает

1. Проверьте токен в `.env`
2. Убедитесь, что бот запущен: `curl http://localhost:8000/status`
3. Проверьте логи: `tail -f /tmp/telegram_bot.log`

### Avito показывает капчу

**Решение:**
1. Войти в Avito через браузер
2. Импортировать cookies: `python scripts/avito_oauth.py`
3. Или использовать OAuth API

### Ошибка базы данных

```bash
# Переинициализация БД
rm data/recruitment.db
python -m common.init_db
```

## 📝 Документация

- `docs/AVITO_SETUP.md` — Настройка Avito
- `docs/WEBAPP.md` — Telegram Web App
- `docs/CLASSIFIEDS_AGENT.md` — Доски объявлений

## 🔐 Безопасность

- Не коммитьте `.env` в git
- Используйте HTTPS для продакшена
- Ограничьте доступ к API

## 📄 Лицензия

MIT

---

**Сделано с ❤️ для автоматизации рекрутинга**
