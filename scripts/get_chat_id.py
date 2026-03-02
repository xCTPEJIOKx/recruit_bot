#!/usr/bin/env python3
"""
Скрипт для получения вашего Telegram Chat ID
Запустите один раз, чтобы получить ID для уведомлений
"""
import requests
import sys

# Читаем токен из .env
from common import settings

if not settings.telegram_bot_token:
    print("❌ TELEGRAM_BOT_TOKEN не найден в .env")
    sys.exit(1)

print("🔍 Получение Chat ID...")
print()

# Метод 1: Через getUpdates (если вы писали боту)
print("📡 Метод 1: Проверка последних сообщений от бота...")
url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    if data.get('result'):
        for update in data['result'][-5:]:  # Последние 5 сообщений
            if 'message' in update:
                chat = update['message'].get('chat', {})
                chat_id = chat.get('id')
                first_name = chat.get('first_name', '')
                username = chat.get('username', '')
                
                if chat_id:
                    print(f"\n✅ Найден Chat ID:")
                    print(f"   ID: {chat_id}")
                    print(f"   Имя: {first_name}")
                    print(f"   Username: @{username}")
                    print()
                    print(f"📝 Добавьте в .env:")
                    print(f"   TELEGRAM_ADMIN_CHAT_ID={chat_id}")
                    sys.exit(0)

# Метод 2: Инструкция
print()
print("❌ Не найдено сообщений от бота.")
print()
print("📋 Инструкция по получению Chat ID:")
print()
print("1. Откройте Telegram и найдите своего бота")
print("2. Нажмите /start или напишите любое сообщение")
print("3. Откройте в браузере:")
print(f"   https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates")
print("4. Найдите в JSON поле 'chat' → 'id'")
print("5. Скопируйте числовое значение")
print()
print("📝 Или используйте бота @userinfobot:")
print("   1. Найдите @userinfobot в Telegram")
print("   2. Нажмите /start")
print("   3. Бот отправит ваш ID")
print()
