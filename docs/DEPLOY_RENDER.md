# 🚀 Деплой на Render.com

Автоматическое развертывание системы рекрутинга на Render.com (бесплатно, 24/7)

## 📋 Что будет развернуто

| Сервис | Тип | Порт | Назначение |
|--------|-----|------|------------|
| recruit-orchestrator | Web | 8000 | API + Dashboard |
| recruit-telegram-bot | Web | - | Telegram бот |
| recruit-avito-agent | Worker | - | Публикация на Avito |
| recruit-voice-agent | Worker | - | Голосовые звонки |

## 🔧 Подготовка

### 1. Создайте аккаунт на Render
- Перейдите на https://render.com
- Зарегистрируйтесь через GitHub

### 2. Подключите репозиторий
- В личном кабинете нажмите **"New +"** → **"Blueprint"**
- Выберите репозиторий: `xCTPEJIOKx/recruit_bot`
- Нажмите **"Connect"**

### 3. Настройте переменные окружения

В разделе **Environment** добавьте:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# Avito
AVITO_LOGIN=+79990000000
AVITO_PASSWORD=ваш_пароль

# Voximplant (опционально)
VOXIMPLANT_ACCOUNT_ID=54675
VOXIMPLANT_API_KEY=ваш_api_key
```

### 4. Запустите деплой
- Нажмите **"Apply"**
- Дождитесь завершения сборки (~5 минут)

## 🌐 URLs после деплоя

```
Orchestrator API:  https://recruit-orchestrator.onrender.com
Dashboard:         https://recruit-orchestrator.onrender.com/candidates
Web App:           https://recruit-orchestrator.onrender.com/static/index.html
```

## 📱 Настройка Telegram Web App

1. Откройте @BotFather
2. `/mybots` → ваш бот → `Bot Settings` → `Menu Button`
3. Укажите URL: `https://recruit-orchestrator.onrender.com/static/index.html`

## 🔄 Авто-обновление

При каждом пуше в ветку `main`:
- Render автоматически пересоберёт сервисы
- Обновление займёт 2-3 минуты

## 📊 Мониторинг

- **Логи:** Render Dashboard → Logs
- **Метрики:** Render Dashboard → Metrics
- **Уведомления:** Settings → Notifications

## 💰 Тарифы

**Free план:**
- 750 часов/месяц бесплатно
- 512 MB RAM на сервис
- Автоматическая спячка при простое

**Pro план ($7/мес):**
- Без спячки
- 2 GB RAM
- Приоритет в очереди

## 🛠️ Troubleshooting

### Сервис не запускается
```bash
# Проверьте логи в Render Dashboard
# Убедитесь, что все переменные окружения заданы
```

### База данных не сохраняется
```bash
# Убедитесь, что диск подключён:
# render.yaml → disk → mountPath: /opt/render/project/src/data
```

### Бот не отвечает
```bash
# Проверьте TELEGRAM_BOT_TOKEN
# Убедитесь, что сервис recruit-telegram-bot работает
```

## 📈 Масштабирование

Для больших нагрузок:

1. **PostgreSQL:** Замените SQLite на Render PostgreSQL
2. **Redis:** Добавьте для кэширования
3. **Docker:** Используйте Dockerfile для кастомной сборки

```yaml
# render.yaml для Docker
services:
  - type: web
    name: recruit-orchestrator
    env: docker
    dockerfilePath: ./Dockerfile
```

## 🔐 Безопасность

- Не коммитьте `.env` в git
- Используйте Render Secrets для токенов
- Включите HTTPS (автоматически на Render)

---

**Поддержка:** Создайте issue в репозитории
