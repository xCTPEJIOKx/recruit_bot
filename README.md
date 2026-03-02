# 🤖 Recruitment System

Автоматизированная система рекрутинга с Web App для Telegram.

## 📋 Архитектура

```
┌─────────────────┐     ┌─────────────────┐
│  Telegram Bot   │────▶│   Web App       │
│  @Recruit2026   │     │  (GitHub Pages) │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Localtunnel/ngrok     │
                    │   (публичный API)       │
                    └────────┬────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    ▼                    │
        │  ┌──────────────────────────┐          │
        └─▶│  Orchestrator (API)      │◀─────────┘
           │  Port: 8000              │
           │  - REST API              │
           │  - Web App (static)      │
           └───────────┬──────────────┘
                       │
           ┌───────────┼──────────────┐
           ▼           ▼              ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │Database  │ │Telegram  │ │ Voice    │
    │SQLite    │ │Bot       │ │ Agent    │
    └──────────┘ └──────────┘ └──────────┘
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd /home/hp/recruitment_agents

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Зависимости
pip install -r requirements.txt
```

### 2. Настройка

```bash
# Копирование .env
cp .env.example .env

# Редактирование .env
nano .env
```

**Обязательные переменные:**
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id  # Запустите: python scripts/get_chat_id.py

# Database
DATABASE_PATH=./data/recruitment.db
```

### 3. Инициализация БД

```bash
python -m common.init_db
```

### 4. Запуск системы

```bash
python run.py
```

**После запуска:**
- API: http://localhost:8000
- Web App: http://localhost:8000/static/index.html
- Dashboard: http://localhost:8000/candidates

### 5. Публикация Web App

**Вариант A: Localtunnel (быстро)**
```bash
lt --port 8080
# Скопируйте URL и обновите app.js
```

**Вариант B: GitHub Pages**
1. Обновите `app.js` с публичным API URL
2. Закоммитьте файлы
3. GitHub Pages автоматически опубликует

### 6. Настройка Telegram бота

1. @BotFather → `/mybots` → Recruit2026_bot
2. Bot Settings → Menu Button
3. Configure Menu Button
4. URL: `https://your-username.github.io/recruit_bot/index.html`

## 📁 Структура проекта

```
recruitment_agents/
├── common/                 # Общие модули
│   ├── config.py          # Настройки
│   ├── database.py        # База данных
│   ├── models.py          # Модели
│   └── init_db.py         # Инициализация БД
├── telegram_bot/          # Telegram бот
│   └── bot.py            # Aiogram бот
├── voice_agent/           # Voice агент
│   └── voice_agent.py    # Голосовые звонки
├── orchestrator/          # API + Web App
│   └── orchestrator.py   # FastAPI
├── web_dashboard/         # Web App
│   └── static/           # HTML/CSS/JS
├── scripts/               # Скрипты
│   ├── run_web.py        # Запуск Web App
│   ├── get_chat_id.py    # Получение chat_id
│   └── create_vacancies.py
├── data/                  # База данных
├── run.py                 # Запуск системы
└── requirements.txt       # Зависимости
```

## 📊 Воронка рекрутинга

```
🆕 Новый → 📞 Связались → ✅ Квалифицирован → 📅 Собеседование → 📋 Offer → 🎉 Принят
```

## 🔧 API Endpoints

| Endpoint | Описание |
|----------|----------|
| `GET /health` | Проверка здоровья |
| `GET /vacancies` | Список вакансий |
| `POST /vacancies` | Создание вакансии |
| `GET /candidates` | Список кандидатов |
| `POST /candidates` | Создание кандидата |
| `PUT /candidates/{id}/status` | Обновление статуса |

## 📱 Web App

Web App открывается в Telegram и позволяет:
- Просматривать вакансии
- Заполнять форму отклика (5 шагов)
- Отправлять данные кандидата

**После отклика:**
- Данные сохраняются в базу
- Telegram уведомление отправляется администратору
- Voice Agent может позвонить кандидату

## 🛠️ Скрипты

### Получить chat_id Telegram
```bash
python scripts/get_chat_id.py
```

### Создать тестовые вакансии
```bash
python scripts/create_vacancies.py
```

### Запустить Web Dashboard
```bash
python scripts/run_web.py
```

## 📈 Мониторинг

### Проверка статуса
```bash
curl http://localhost:8000/health
curl http://localhost:8000/status
curl http://localhost:8000/stats
```

### Логи
```bash
tail -f /tmp/orch.log    # Orchestrator
tail -f /tmp/tg.log      # Telegram Bot
tail -f /tmp/voice.log   # Voice Agent
```

## 🔐 Безопасность

- Не коммитьте `.env` в git
- Используйте HTTPS для продакшена
- Ограничьте доступ к API

## 📄 Лицензия

MIT
