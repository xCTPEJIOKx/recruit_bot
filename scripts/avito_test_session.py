#!/usr/bin/env python3
"""
Avito Session Test — Проверка и сохранение рабочей сессии
"""
import asyncio
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, '/home/hp/recruitment_agents')

from playwright.async_api import async_playwright

async def test_session():
    print("="*60)
    print("🔐 Avito Session Test")
    print("="*60)
    
    # Проверяем сессию
    session_file = Path("/tmp/avito_session.json")
    if session_file.exists():
        with open(session_file, 'r') as f:
            cookies = json.load(f)
        print(f"✅ Сессия найдена: {len(cookies)} cookies")
    else:
        print("❌ Сессия не найдена")
        return False
    
    print("\n🌐 Запуск браузера...")
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    # Загружаем сессию
    await context.add_cookies(cookies)
    page = await context.new_page()
    
    print("🔐 Проверка авторизации...")
    await page.goto("https://www.avito.ru/profile", wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)
    
    # Проверяем вошли ли
    try:
        profile_link = await page.query_selector('a[href="/user_profile"]')
        if profile_link:
            print("✅ Сессия РАБОЧАЯ! Вы вошли в Avito.")
            
            # Сохраняем обновлённые cookies
            new_cookies = await context.cookies()
            with open(session_file, 'w') as f:
                json.dump(new_cookies, f, indent=2)
            print(f"💾 Сессия обновлена: {len(new_cookies)} cookies")
            
            await browser.close()
            return True
        else:
            print("❌ Сессия НЕ РАБОЧАЯ. Требуется новый вход.")
    except:
        print("❌ Ошибка проверки сессии")
    
    await browser.close()
    
    # Если сессия не рабочая — сохраняем новую
    print("\n📋 Для сохранения новой сессии:")
    print("   1. Откройте браузер: chromium-browser")
    print("   2. Войдите на https://www.avito.ru")
    print("   3. Скопируйте cookies из DevTools")
    print("   4. Или используйте:")
    print("      python scripts/avito_save_session.py")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_session())
    sys.exit(0 if success else 1)
