# 🚀 DEPLOYMENT НА RENDER.COM

Полная инструкция по развертыванию системы на Render.com (бесплатно, 24/7)

---

## 📋 ЧТО БУДЕТ РАЗВЕРНУТО

| Сервис | Тип | Назначение |
|--------|-----|------------|
| recruit-orchestrator | Web | API + Web App (порт 8000) |
| recruit-telegram-bot | Worker | Telegram бот |
| recruit-voice-agent | Worker | Voice Agent (звонки) |

---

## 🔧 ПОДГОТОВКА

### 1. Создайте аккаунт на Render

1. Перейдите на https://render.com
2. Нажмите **"Get Started for Free"**
3. Войдите через GitHub

### 2. Подготовьте репозиторий

Убедитесь, что все файлы отправлены на GitHub:

```bash
cd /home/hp/recruitment_agents
git add -A
git commit -m "Prepare for Render deployment"
git push origin main
```

---

## 📤 ДЕПЛОЙ

### Вариант 1: Blueprint (рекомендуется)

1. **Откройте Render Dashboard**
   ```
   https://dashboard.render.com
   ```

2. **Создайте Blueprint**
   - Нажмите **"New +"** → **"Blueprint"**
   - Выберите репозиторий: `xCTPEJIOKx/recruit_bot`
   - Нажмите **"Connect"**

3. **Добавьте переменные окружения**

   В разделе **Environment** добавьте:

   | Ключ | Значение |
   |------|----------|
   | `TELEGRAM_BOT_TOKEN` | `8546310725:AAGkqmkjFp_DfMFKqA75Q0IXV8xuEU3JaNA` |
   | `TELEGRAM_ADMIN_CHAT_ID` | `8197222276` |
   | `VOXIMPLANT_ACCOUNT_ID` | `54675` |
   | `VOXIMPLANT_API_KEY` | `486ba90d76807592a376b8fb355d8fb84802c8413c61afc657f73e69d3c0665e` |

4. **Нажмите "Apply"**

5. **Ждите 5-10 минут**

   Render автоматически создаст 3 сервиса из `render.yaml`

---

### Вариант 2: Docker (альтернатива)

1. **Создайте Web Service**
   - Dashboard → **"New +"** → **"Web Service"**
   - Выберите репозиторий: `xCTPEJIOKx/recruit_bot`
   - Configure:
     - **Name:** `recruit-orchestrator`
     - **Region:** Frankfurt (Germany)
     - **Branch:** `main`
     - **Root Directory:** (оставьте пустым)
     - **Runtime:** Docker
     - **DockerfilePath:** `./Dockerfile`
     - **Plan:** Free

2. **Добавьте переменные окружения** (как выше)

3. **Добавьте Disk**
   - Name: `recruit-data`
   - Mount Path: `/app/data`
   - Size: 1 GB

4. **Deploy!**

---

## 🌐 URL ПОСЛЕ ДЕПЛОЯ

После успешного деплоя вы получите:

```
Orchestrator API:  https://recruit-orchestrator-xxxx.onrender.com
Web App:           https://recruit-orchestrator-xxxx.onrender.com/static/index.html
Dashboard:         https://recruit-orchestrator-xxxx.onrender.com/dashboard
API:               https://recruit-orchestrator-xxxx.onrender.com/api
```

---

## 📱 НАСТРОЙКА TELEGRAM

### 1. Обновите Menu Button

1. Откройте @BotFather
2. `/mybots` → `Recruit2026_bot`
3. `Bot Settings` → `Menu Button`
4. `Configure Menu Button`
5. Отправьте URL:
   ```
   https://recruit-orchestrator-xxxx.onrender.com/static/index.html
   ```
6. Название: `📝 Откликнуться`

### 2. Проверьте уведомления

Убедитесь, что `TELEGRAM_ADMIN_CHAT_ID=8197222276` задан

---

## 🔄 АВТО-ОБНОВЛЕНИЕ

При каждом `git push`:

1. Render обнаруживает изменения
2. Автоматически пересобирает сервисы
3. Обновляет без простоя (2-3 минуты)

**Ничего делать не нужно!**

---

## 📊 МОНИТОРИНГ

### Логи
```
Dashboard → Сервис → Logs
```

### Метрики
```
Dashboard → Сервис → Metrics
```

### Уведомления
```
Settings → Notifications → Email
```

---

## 💰 ТАРИФЫ

### Free план (используем)
- ✅ 750 часов/месяц бесплатно
- ✅ 512 MB RAM на сервис
- ✅ 1 GB диск бесплатно
- ⚠️ Автоматическая спячка при 15 мин простоя

### Pro план ($7/мес за сервис)
- ✅ Без спячки
- ✅ 2 GB RAM
- ✅ Приоритет в очереди

---

## 🛠️ TROUBLESHOOTING

### Сервис не запускается

**Проверьте логи:**
```
Dashboard → recruit-orchestrator → Logs
```

**Частые ошибки:**
- ❌ Нет переменных окружения → Добавьте из таблицы выше
- ❌ Ошибка базы данных → Проверьте Disk mount path
- ❌ Порт не настроен → Render использует `$PORT` автоматически

### Бот не отвечает

1. Проверьте `TELEGRAM_BOT_TOKEN`
2. Проверьте логи: `recruit-telegram-bot → Logs`
3. Убедитесь, что сервис работает (статус "Live")

### Web App не открывается

1. Проверьте URL (должен быть `https://...onrender.com`)
2. Подождите 2-3 минуты (Render "просыпается")
3. Проверьте логи orchestrator

### База данных не сохраняется

Убедитесь, что Disk подключён:
```yaml
disk:
  name: recruit-data
  mountPath: /opt/render/project/src/data
  sizeGB: 1
```

---

## 📈 МАСШТАБИРОВАНИЕ

Для больших нагрузок:

### 1. PostgreSQL
Замените SQLite на Render PostgreSQL:

```yaml
databases:
  - name: recruit-db
    databaseName: recruitment
    user: recruit_user
```

### 2. Redis
Добавьте для кэширования:

```yaml
redis:
  - name: recruit-cache
    plan: free
```

### 3. Увеличьте план
```yaml
plan: starter  # $7/мес
```

---

## 🔐 БЕЗОПАСНОСТЬ

- ✅ HTTPS автоматически
- ✅ Переменные окружения шифруются
- ✅ Disk изолирован
- ⚠️ Не коммитьте `.env` в git

---

## ✅ ЧЕКЛИСТ ДЕПЛОЯ

- [ ] Аккаунт Render создан
- [ ] Репозиторий подключён
- [ ] `render.yaml` в репозитории
- [ ] Переменные окружения добавлены
- [ ] Disk подключён (1 GB)
- [ ] Деплой запущен
- [ ] Все сервисы "Live"
- [ ] Web App открывается
- [ ] Telegram бот отвечает
- [ ] Menu Button настроен

---

**Готово! Система работает 24/7!** 🎉

**Поддержка:** Создайте issue в репозитории
