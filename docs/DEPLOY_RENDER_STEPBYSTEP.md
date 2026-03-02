# 🚀 ДЕПЛОЙ НА RENDER.COM - ПОШАГОВАЯ ИНСТРУКЦИЯ

## 📋 Шаг 1: Войдите в Render

1. Откройте: **https://render.com**
2. Нажмите **"Get Started for Free"**
3. Выберите **"Sign in with GitHub"**
4. Авторизуйтесь через ваш GitHub аккаунт

---

## 📋 Шаг 2: Создайте новый сервис

### 2.1 В Dashboard нажмите **"New +"**

### 2.2 Выберите **"Blueprint"**

### 2.3 Подключите репозиторий
- Найдите: **`xCTPEJIOKx/recruit_bot`**
- Нажмите **"Connect"**

---

## 📋 Шаг 3: Настройте переменные окружения

В разделе **"Environment"** добавьте следующие переменные:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=8546310725:AAGkqmkjFp_DfMFKqA75Q0IXV8xuEU3JaNA
TELEGRAM_ADMIN_CHAT_ID=819222276

# Avito
AVITO_LOGIN=+79538765405
AVITO_PASSWORD=CTPEJIOK77z.

# Voximplant
VOXIMPLANT_ACCOUNT_ID=54675
VOXIMPLANT_API_KEY=486ba90d76807592a376b8fb355d8fb84802c8413c61afc657f73e69d3c0665e

# База данных
DATABASE_PATH=/opt/render/project/src/data/recruitment.db

# Orchestrator
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=10000

# Логирование
LOG_LEVEL=INFO
DEBUG=false
```

**Важно:**
- `ORCHESTRATOR_PORT=10000` - Render использует динамические порты
- `DATABASE_PATH` - путь к диску Render

---

## 📋 Шаг 4: Настройте диск для данных

В разделе **"Disks"** нажмите **"Add Disk"**:

- **Name:** `recruit-data`
- **Mount Path:** `/opt/render/project/src/data`
- **Size:** `1 GB` (бесплатно)

---

## 📋 Шаг 5: Запустите деплой

1. Прокрутите вниз
2. Нажмите **"Apply"**
3. Ждите 5-10 минут

Render автоматически создаст 4 сервиса из `render.yaml`:
- ✅ recruit-orchestrator (Web)
- ✅ recruit-telegram-bot (Worker)
- ✅ recruit-avito-agent (Worker)
- ✅ recruit-voice-agent (Worker)

---

## 📋 Шаг 6: Проверьте статус

В Dashboard Render вы увидите:

```
┌─────────────────────────────┬─────────┬──────────────────────┐
│ Service                     │ Status  │ URL                  │
├─────────────────────────────┼─────────┼──────────────────────┤
│ recruit-orchestrator        │ Live    │ https://xxx.onrender.com │
│ recruit-telegram-bot        │ Live    │ -                    │
│ recruit-avito-agent         │ Live    │ -                    │
│ recruit-voice-agent         │ Live    │ -                    │
└─────────────────────────────┴─────────┴──────────────────────┘
```

---

## 📋 Шаг 7: Настройте Telegram бота

### 7.1 Откройте @BotFather

### 7.2 Настройте Menu Button:
```
/mybots → Recruit2026_bot → Bot Settings → Menu Button → Configure Menu Button
```

### 7.3 Отправьте URL:
```
https://recruit-orchestrator.onrender.com/static/index.html
```

(Замените `recruit-orchestrator` на ваше название сервиса)

### 7.4 Дайте название кнопке:
```
📝 Откликнуться
```

---

## ✅ ГОТОВО!

**Система работает 24/7:**

| Сервис | URL |
|--------|-----|
| **Dashboard** | `https://recruit-orchestrator.onrender.com/candidates` |
| **Web App** | `https://recruit-orchestrator.onrender.com/static/index.html` |
| **API** | `https://recruit-orchestrator.onrender.com` |

---

## 📊 Проверка работы

### 1. Откройте Web App
- Нажмите кнопку меню в Telegram боте
- Или откройте URL напрямую

### 2. Заполните форму
- Пройдите 5 шагов квалификации

### 3. Проверьте Telegram
- Вам придёт уведомление с данными кандидата

### 4. Проверьте Dashboard
- Кандидат появится в списке

---

## 🔧 Troubleshooting

### Сервис не запускается

**Проверьте логи:**
```
Render Dashboard → recruit-orchestrator → Logs
```

**Частые ошибки:**
- ❌ Нет переменных окружения → Добавьте все из Шага 3
- ❌ Ошибка базы данных → Проверьте путь к диску
- ❌ Порт не настроен → `ORCHESTRATOR_PORT=10000`

### Бот не отвечает

1. Проверьте `TELEGRAM_BOT_TOKEN`
2. Проверьте логи: `recruit-telegram-bot → Logs`
3. Убедитесь, что сервис работает (статус "Live")

### Web App не открывается

1. Проверьте URL (должен быть `https://...onrender.com`)
2. Подождите 2-3 минуты (Render "просыпается")
3. Проверьте логи orchestrator

---

## 💰 Тарифы Render

**Free план:**
- ✅ 750 часов/месяц (хватит на 4 сервиса)
- ✅ 512 MB RAM на сервис
- ✅ 1 GB диск бесплатно
- ⚠️ Спячка при простое (30 мин)

**Pro план ($7/мес):**
- ✅ Без спячки
- ✅ 2 GB RAM
- ✅ Приоритет в очереди

---

## 🔄 Авто-обновление

При каждом `git push` в ветку `main`:
1. Render автоматически обнаружит изменения
2. Пересоберёт все сервисы
3. Обновит без простоя (2-3 минуты)

---

## 📈 Мониторинг

### Логи
```
Render Dashboard → Сервис → Logs
```

### Метрики
```
Render Dashboard → Сервис → Metrics
```

### Уведомления
```
Settings → Notifications → Email/SMS
```

---

## 🆘 Помощь

- **Документация Render:** https://render.com/docs
- **Статус Render:** https://status.render.com
- **Поддержка:** support@render.com

---

**Всё готово! Система работает 24/7! 🎉**
