# 🚀 Быстрый старт - Деплой на Render

## ⚡ 5 шагов для запуска 24/7

### Шаг 1: Аккаунт на Render
1. Перейдите на https://render.com
2. Нажмите **"Get Started for Free"**
3. Войдите через GitHub

### Шаг 2: Подключите репозиторий
1. В Dashboard нажмите **"New +"**
2. Выберите **"Blueprint"**
3. Найдите репозиторий: `xCTPEJIOKx/recruit_bot`
4. Нажмите **"Connect"**

### Шаг 3: Добавьте переменные окружения

В разделе **Environment** добавьте:

| Ключ | Значение |
|------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен из @BotFather |
| `AVITO_LOGIN` | +79990000000 |
| `AVITO_PASSWORD` | Пароль от Avito |
| `VOXIMPLANT_ACCOUNT_ID` | 54675 |
| `VOXIMPLANT_API_KEY` | Ваш API ключ |

### Шаг 4: Деплой
1. Нажмите **"Apply"**
2. Ждите 5-7 минут
3. Все 4 сервиса запустятся

### Шаг 5: Настройте бота
1. Откройте @BotFather
2. `/mybots` → ваш бот
3. `Bot Settings` → `Menu Button` → `Configure Menu Button`
4. Отправьте URL: `https://recruit-orchestrator.onrender.com/static/index.html`

---

## ✅ Готово!

**Система работает 24/7:**
- ✅ Orchestrator API
- ✅ Telegram бот
- ✅ Avito агент
- ✅ Voice агент

**URL:**
- Dashboard: `https://recruit-orchestrator.onrender.com/candidates`
- Web App: `https://recruit-orchestrator.onrender.com/static/index.html`
- API: `https://recruit-orchestrator.onrender.com`

---

## 📊 Авто-обновление

При каждом `git push`:
- Render автоматически обновит сервисы
- Простой: 2-3 минуты

---

## 💰 Бесплатный тариф

- 750 часов/месяц (хватит на 4 сервиса)
- 512 MB RAM на сервис
- Автоматическая спячка при простое

---

## 🆘 Помощь

- [Полная документация](DEPLOY_RENDER.md)
- [Render Docs](https://render.com/docs)
- GitHub Issues
