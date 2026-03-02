# 📢 Classifieds Agent - Автопостинг на доски объявлений

## 🎯 Назначение

Автоматическая публикация вакансий на бесплатные доски объявлений для максимального охвата кандидатов.

---

## 📋 Поддерживаемые площадки

### Бесплатные:

| Площадка | URL | Статус |
|----------|-----|--------|
| **Farpost** | farpost.ru | ✅ Работает |
| **Youla** | youla.ru | ✅ Работает |
| **Drom.ru Работа** | drom.ru/work | ✅ Работает |
| **IRR.ru** | irr.ru | ✅ Работает |
| **GorodRabot** | gorodrabot.ru | ⚠️ Требуется настройка |
| **Rabota.ru** | rabota.ru | ⚠️ Требуется настройка |
| **Zarplata.ru** | zarplata.ru | ⚠️ Требуется настройка |

### Платные (требуется подписка):

| Площадка | URL | Стоимость |
|----------|-----|-----------|
| **Avito** | avito.ru | от 500 ₽/вакансия |
| **HH.ru** | hh.ru | от 3000 ₽/мес |
| **SuperJob** | superjob.ru | от 5000 ₽/мес |

---

## 🚀 Установка

### 1. Установите зависимости:

```bash
pip install selenium webdriver-manager
```

### 2. Установите ChromeDriver:

```bash
# Автоматически через webdriver-manager
python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"

# Или вручную скачайте с https://chromedriver.chromium.org
```

### 3. Запустите агента:

```bash
cd /home/hp/recruitment_agents
python -m classifieds_agent.agent
```

---

## ⚙️ Настройка

### Базовая конфигурация:

```python
agent = ClassifiedsAgent(
    headless=True,  # Режим без GUI
)

# Настройки
agent.max_posts_per_day = 50  # Лимит постов в день
agent.post_interval = 60  # Интервал между постами (сек)
```

### Площадки для постинга:

Отредактируйте `CLASSIFIEDS_PLATFORMS` в `agent.py`:

```python
CLASSIFIEDS_PLATFORMS = {
    "farpost": {
        "name": "Farpost",
        "url": "https://www.farpost.ru",
        "free": True,
        "requires_auth": False,
    },
    # ... другие площадки
}
```

---

## 📊 Как это работает:

### Поток постинга:

```
1. Получение активных вакансий из БД
   ↓
2. Проверка дневного лимита
   ↓
3. Для каждой вакансии:
   ├─ Farpost → заполнение формы
   ├─ Youla → заполнение формы
   ├─ Drom → заполнение формы
   └─ IRR → заполнение формы
   ↓
4. Пауза 60 секунд
   ↓
5. Повтор цикла
```

### Автоматизация:

- **Selenium WebDriver** — автоматизация браузера
- **Headless режим** — работа без GUI
- **Auto-retry** — повтор при ошибках
- **Лимиты** — защита от бана

---

## 🔧 Использование

### Запуск агента:

```bash
# В фоне
nohup python -m classifieds_agent.agent > /tmp/classifieds.log 2>&1 &

# Проверка статуса
ps aux | grep classifieds
```

### Проверка статистики:

```python
from classifieds_agent import ClassifiedsAgent

agent = ClassifiedsAgent()
stats = await agent.get_stats()

print(f"Постов сегодня: {stats['posts_today']}")
print(f"Всего постов: {stats['posts_total']}")
print(f"Ошибок: {stats['errors']}")
print(f"Площадок: {stats['platforms']}")
```

---

## 📈 Статистика постинга:

| Метрика | Значение |
|---------|----------|
| Постов в день (макс) | 50 |
| Интервал между постами | 60 сек |
| Площадок всего | 10 |
| Бесплатных площадок | 7 |
| Время на пост | ~30 сек |

---

## ⚠️ Важные заметки:

### Лимиты и ограничения:

1. **Дневной лимит** — 50 постов (настраивается)
2. **Интервал** — 60 секунд между постами
3. **User-Agent** — рандомизируется
4. **IP адрес** — используйте прокси при необходимости

### Безопасность:

- Не постите одинаковый контент слишком часто
- Используйте разные заголовки
- Делайте перерывы между постами
- Мониторьте баны

---

## 🐛 Troubleshooting:

### "ChromeDriver not found"

```bash
# Установите ChromeDriver
pip install webdriver-manager
python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

### "Element not found"

Структура сайта изменилась. Обновите селекторы в коде:

```python
# Найдите правильный селектор через DevTools
# Замените:
self.driver.find_element(By.NAME, "title")
# На правильный селектор
```

### "Too Many Requests"

Увеличьте интервал:

```python
agent.post_interval = 120  # 2 минуты
```

---

## 💡 Советы:

1. **Запускайте в headless режиме** — меньше ресурсов
2. **Используйте прокси** — для обхода лимитов
3. **Мониторьте логи** — для отлова ошибок
4. **Обновляйте вакансии** — раз в 3-7 дней
5. **A/B тестируйте** — разные заголовки

---

## 📚 API Площадок:

### Farpost (бесплатно, без регистрации):

```python
POST https://www.farpost.ru/vacancies/add/
Параметры:
  - title: Название вакансии
  - text: Описание
  - price: Зарплата
  - contact: Контакты
```

### Youla (требуется регистрация):

```python
POST https://youla.ru/moskva/uslugi/new
Требуется авторизация
```

---

## 🎯 Интеграция с системой:

Агент автоматически:
- Получает вакансии из общей БД
- Отправляет heartbeat в Orchestrator
- Логирует взаимодействия

---

**Готово к использованию!** 🚀
