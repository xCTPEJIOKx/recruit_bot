# 🔐 Avito Авторизация - Решение проблемы

## ❌ Проблема

Avito Browser Agent не может войти в аккаунт, потому что:
1. Avito показывает **капчу** при автоматическом входе
2. Нет сохранённой сессии
3. Headless браузер не может решить капчу

---

## ✅ Решение 1: Импорт cookies из вашего браузера (РЕКОМЕНДУЕТСЯ)

### Шаг 1: Войдите в Avito на своём компьютере

1. Откройте Chrome или Firefox
2. Перейдите на https://www.avito.ru
3. Войдите в аккаунт (логин: `+79538765405`)
4. Решите капчу если появится

### Шаг 2: Скопируйте cookies

**Chrome:**
1. Нажмите `F12` (DevTools)
2. Перейдите во вкладку **Application**
3. Раскройте **Cookies** → **https://www.avito.ru**
4. Выделите все cookies (`Ctrl+A`)
5. Скопируйте (`Ctrl+C`)

**Firefox:**
1. Нажмите `F12` (DevTools)
2. Перейдите во вкладку **Storage**
3. Раскройте **Cookies** → **https://www.avito.ru**
4. Выделите все cookies
5. Скопируйте

### Шаг 3: Вставьте cookies на сервере

```bash
cd /home/hp/recruitment_agents
source venv/bin/activate

# Запустите импорт
python scripts/avito_session_import.py
```

Скрипт попросит вставить cookies - вставьте скопированный JSON.

**ИЛИ** создайте файл вручную:

```bash
# На своём компьютере экспортируйте cookies в файл
# Затем скопируйте на сервер:
scp avito_cookies.json user@server:/tmp/avito_session.json
```

### Шаг 4: Перезапустите Avito агента

```bash
# Убить старый процесс
pkill -f avito_browser_agent

# Запустить заново
cd /home/hp/recruitment_agents
source venv/bin/activate
python scripts/run_avito_browser.py &
```

---

## ✅ Решение 2: Использование Chrome на сервере с X11

Если на сервере есть X11:

```bash
# Установите xvfb
sudo apt-get install xvfb

# Запустите с виртуальным дисплеем
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Запустите скрипт сохранения
python scripts/save_avito_session_interactive.py
```

Затем подключитесь через VNC для решения капчи.

---

## ✅ Решение 3: Avito OAuth API (для продакшена)

### Регистрация приложения

1. Перейдите на https://api.avito.ru
2. Создайте аккаунт разработчика
3. Создайте OAuth приложение

### Получение токенов

```bash
cd /home/hp/recruitment_agents
source venv/bin/activate
python scripts/avito_oauth.py
```

### Добавление в .env

```bash
# Avito API
AVITO_CLIENT_ID=your_client_id
AVITO_CLIENT_SECRET=your_client_secret
AVITO_ACCESS_TOKEN=your_access_token
AVITO_REFRESH_TOKEN=your_refresh_token
```

### Запуск API агента

Обновите `run.py`:

```python
from avito_agent import run_avito_agent  # API агент
# вместо
from avito_agent.avito_browser_agent import run_avito_browser_agent
```

---

## 🔍 Проверка сессии

```bash
# Проверить файл сессии
cat /tmp/avito_session.json | python3 -m json.tool

# Проверить количество cookies
python3 -c "import json; print(len(json.load(open('/tmp/avito_session.json'))))"

# Протестировать вход
python scripts/run_avito_browser.py
```

---

## 📊 Текущий статус

| Метод | Статус | Примечание |
|-------|--------|------------|
| **Browser Agent** | ⚠️ Ждёт сессию | Нужно импортировать cookies |
| **API Agent** | ❌ Не настроен | Нужны OAuth токены |
| **Симуляция** | ✅ Работает | Создаёт тестовых кандидатов |

---

## 🚀 Быстрое решение (прямо сейчас)

```bash
# 1. На своём компьютере войдите на Avito и скопируйте cookies
# 2. На сервере:

cd /home/hp/recruitment_agents

# Создайте файл с cookies (вставьте свой JSON)
cat > /tmp/avito_session.json << 'EOF'
[
  {"name": "avito_sid", "value": "YOUR_SESSION_ID", "domain": ".avito.ru", "path": "/"},
  ...
]
EOF

# Перезапустите агента
pkill -f avito_browser_agent
source venv/bin/activate
python scripts/run_avito_browser.py &
```

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `tail -f /tmp/avito_browser.log`
2. Проверьте сессию: `ls -la /tmp/avito_session.json`
3. Проверьте вход вручную: `curl -H "Cookie: avito_sid=XXX" https://www.avito.ru/profile`
